import os
from dotenv import load_dotenv
import stripe
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict
from datetime import datetime, timedelta
from models.payment.payment_models import (
    Subscription, Transaction, Payment, PaymentStatus,
    SubscriptionCreate, SubscriptionResponse,
    TransactionCreate, TransactionResponse
)
from db.db import get_db, init_db, Base
from fastapi.middleware.cors import CORSMiddleware
from services.error_tracking import init_error_tracking, capture_error
import logging
from services.logging_utils import setup_logging

# Initialize logging and error tracking
setup_logging("payment_service")
logger = logging.getLogger(__name__)
init_error_tracking("payment_service")

# Load environment variables
load_dotenv()

# Initialize Stripe with environment variables - SAFE MODE
stripe_api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_dummy_key_for_development')
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_test_dummy_key_for_development')

# Only set if not dummy keys
if stripe_api_key and not stripe_api_key.startswith('sk_test_dummy'):
    stripe.api_key = stripe_api_key
    logger.info("Stripe API key configured")
else:
    logger.warning("Using dummy Stripe keys - payments disabled in development mode")
    stripe.api_key = None

WEBHOOK_SECRET = webhook_secret

app = FastAPI(title="Payment Service")

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Payment service database initialized")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "payment", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}"
        )

# Enhanced error handling
class PaymentError(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

@app.exception_handler(PaymentError)
async def payment_error_handler(request: Request, exc: PaymentError):
    return {
        "status": "error",
        "message": exc.message,
        "code": exc.code
    }

@app.post("/create-payment-intent")
async def create_payment_intent(data: Dict, db: AsyncSession = Depends(get_db)):
    try:
        amount = data.get('amount')
        user_id = data.get('user_id')
        
        if not amount or not user_id:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # If Stripe is not configured, just simulate
        if not stripe.api_key:
            logger.warning(f"Stripe not configured, simulating payment for user {user_id}")
            payment = Payment(
                user_id=user_id,
                amount=amount,
                payment_intent_id=f"sim_{user_id}_{int(datetime.utcnow().timestamp())}",
                status=PaymentStatus.PENDING
            )
            db.add(payment)
            await db.commit()
            return {"clientSecret": "sim_secret"}

        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='usd',
            metadata={'user_id': user_id}
        )

        # Create payment record
        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_intent_id=intent.id,
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        await db.commit()

        return {"clientSecret": intent.client_secret}

    except Exception as e:
        capture_error(e, {"user_id": user_id, "amount": amount})
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not stripe.api_key:
        logger.warning("Webhook received but Stripe not configured")
        return {"status": "success"}
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError as e:
        raise PaymentError(message="Invalid payload", code="INVALID_PAYLOAD")
    except stripe.error.SignatureVerificationError as e:
        raise PaymentError(message="Invalid signature", code="INVALID_SIGNATURE")

    # Enhanced webhook event handling
    try:
        if event["type"] == "payment_intent.succeeded":
            await handle_payment_succeeded(event["data"]["object"], db)
        elif event["type"] == "payment_intent.payment_failed":
            await handle_payment_failed(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_cancelled(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"], db)
    except Exception as e:
        raise PaymentError(
            message=f"Error processing webhook: {str(e)}", 
            code="WEBHOOK_PROCESSING_ERROR"
        )

    return {"status": "success"}

async def handle_payment_succeeded(payment_intent, db: AsyncSession):
    try:
        result = await db.execute(
            select(Transaction).where(
                Transaction.stripe_payment_intent_id == payment_intent["id"]
            )
        )
        transaction = result.scalars().first()
        
        if transaction:
            transaction.status = 'completed'
            transaction.processed_at = datetime.utcnow()
            await db.commit()
            
    except Exception as e:
        await db.rollback()
        raise PaymentError(message=f"Failed to process payment: {str(e)}")

async def handle_payment_failed(payment_intent, db: AsyncSession):
    try:
        result = await db.execute(
            select(Transaction).where(
                Transaction.stripe_payment_intent_id == payment_intent["id"]
            )
        )
        transaction = result.scalars().first()
        
        if transaction:
            transaction.status = 'failed'
            transaction.error_message = payment_intent.get("last_payment_error", {}).get("message")
            await db.commit()
            
    except Exception as e:
        await db.rollback()
        raise PaymentError(message=f"Failed to handle payment failure: {str(e)}")

async def handle_subscription_cancelled(subscription, db: AsyncSession):
    try:
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        db_subscription = result.scalars().first()
        
        if db_subscription:
            db_subscription.is_active = False
            db_subscription.end_date = datetime.utcnow()
            await db.commit()
            
    except Exception as e:
        await db.rollback()
        raise PaymentError(message=f"Failed to handle subscription cancellation: {str(e)}")

async def handle_subscription_updated(subscription, db: AsyncSession):
    try:
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        db_subscription = result.scalars().first()
        
        if db_subscription:
            db_subscription.status = subscription["status"]
            db_subscription.current_period_end = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            await db.commit()
            
    except Exception as e:
        await db.rollback()
        raise PaymentError(message=f"Failed to handle subscription update: {str(e)}")

# Enhanced subscription endpoints
@app.post("/subscriptions/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if user already has an active subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == subscription.user_id,
            Subscription.is_active == True
        )
    )
    active_sub = result.scalars().first()
    
    if active_sub:
        active_sub.is_active = False
        db.add(active_sub)
    
    if not stripe.api_key:
        logger.warning("Stripe not configured, simulating subscription")
        db_subscription = Subscription(**subscription.dict())
        db_subscription.stripe_subscription_id = f"sim_sub_{subscription.user_id}"
        db.add(db_subscription)
        await db.commit()
        await db.refresh(db_subscription)
        return db_subscription
    
    # Create Stripe customer if not exists
    try:
        stripe_customer = stripe.Customer.create(
            metadata={"user_id": subscription.user_id}
        )
        
        # Create Stripe subscription
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer.id,
            items=[{"price": get_stripe_price_id(subscription.plan_type)}],
            metadata={
                "user_id": subscription.user_id,
            }
        )
        
        # Create local subscription
        db_subscription = Subscription(**subscription.dict())
        db_subscription.stripe_subscription_id = stripe_subscription.id
        db.add(db_subscription)
        
        try:
            await db.commit()
            await db.refresh(db_subscription)
        except Exception as e:
            # Cleanup Stripe subscription if DB operation fails
            stripe.Subscription.delete(stripe_subscription.id)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create subscription"
            )
            
        return db_subscription
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.subscription_id == subscription_id
        )
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    try:
        # Cancel Stripe subscription if configured
        if stripe.api_key and subscription.stripe_subscription_id:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update local subscription
        subscription.is_active = False
        subscription.end_date = datetime.utcnow()
        
        await db.commit()
        return {"message": "Subscription cancelled successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not cancel subscription"
        )

# Enhanced transaction endpoints with refund support
@app.post("/transactions/refund/{transaction_id}")
async def refund_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id
        )
    )
    transaction = result.scalars().first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.status != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction cannot be refunded"
        )
    
    try:
        # Process refund through Stripe
        refund = stripe.Refund.create(
            payment_intent=transaction.stripe_payment_intent_id
        )
        
        # Create refund transaction
        refund_transaction = Transaction(
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            amount=-transaction.amount,  # Negative amount for refund
            payment_method=transaction.payment_method,
            status='completed',
            stripe_payment_intent_id=refund.id,
            refund_for_transaction_id=transaction_id
        )
        
        db.add(refund_transaction)
        await db.commit()
        
        return {"message": "Refund processed successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def get_stripe_price_id(plan_type: str) -> str:
    price_map = {
        "premium": "price_premium_monthly",
        "coaching": "price_coaching_monthly"
    }
    return price_map.get(plan_type, "price_free")

@app.get("/subscriptions/user/{user_id}", response_model=SubscriptionResponse)
async def get_active_subscription(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        )
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    return subscription

@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(
            Subscription.subscription_id == subscription_id
        )
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return subscription

@app.post("/transactions/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify subscription exists
    result = await db.execute(
        select(Subscription).where(
            Subscription.subscription_id == transaction.subscription_id
        )
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Create transaction with pending status
    db_transaction = Transaction(
        **transaction.dict(),
        status='pending'
    )
    db.add(db_transaction)
    
    try:
        await db.commit()
        await db.refresh(db_transaction)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create transaction"
        )
    
    # Here you would typically integrate with a payment gateway
    # For demo purposes, we'll just mark it as completed
    db_transaction.status = 'completed'
    try:
        await db.commit()
        await db.refresh(db_transaction)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update transaction status"
        )
    
    return db_transaction

@app.get("/transactions/user/{user_id}", response_model=List[TransactionResponse])
async def get_user_transactions(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id
        ).offset(skip).limit(limit)
    )
    return result.scalars().all()

@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id
        )
    )
    transaction = result.scalars().first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

@app.get("/subscription-plans")
async def get_subscription_plans():
    return {
        "plans": [
            {
                "type": "free",
                "price": 0,
                "features": [
                    "Basic workout tracking",
                    "Manual calorie counting",
                    "Basic meal plans"
                ]
            },
            {
                "type": "premium",
                "price": 9.99,
                "features": [
                    "Advanced workout plans",
                    "Personalized nutrition",
                    "Progress tracking",
                    "Meal suggestions"
                ]
            },
            {
                "type": "coaching",
                "price": 49.99,
                "features": [
                    "All Premium features",
                    "1-on-1 coaching",
                    "Custom workout plans",
                    "Direct chat with PT",
                    "Video consultations"
                ]
            }
        ]
    }

@app.get("/payment-history/{user_id}")
async def get_payment_history(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        payments = result.scalars().all()
        return {"payments": [{"id": p.payment_id, "amount": p.amount, "status": p.status} for p in payments]}
    except Exception as e:
        capture_error(e, {"user_id": user_id})
        logger.error(f"Error fetching payment history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
