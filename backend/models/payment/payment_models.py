from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from db.db import Base
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    payment_intent_id = Column(String(255))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(TIMESTAMP, server_default=func.now())
    processed_at = Column(TIMESTAMP, nullable=True)
    error_message = Column(String(500), nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    subscription_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # No FK constraint to users_db
    plan_type = Column(Enum('free', 'premium', 'coaching', name='subscription_type'))
    start_date = Column(TIMESTAMP, server_default=func.now())
    end_date = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    amount = Column(Float)
    stripe_subscription_id = Column(String(255))
    stripe_customer_id = Column(String(255))
    auto_renew = Column(Boolean, default=True)
    canceled_at = Column(TIMESTAMP, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # No FK constraint to users_db
    subscription_id = Column(Integer, ForeignKey("subscriptions.subscription_id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum('pending', 'completed', 'failed', 'refunded', name='transaction_status'))
    payment_method = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())
    stripe_payment_intent_id = Column(String(255))
    refund_for_transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"), nullable=True)
    transaction_metadata = Column(String(1000))  # JSON string for additional payment data

# Pydantic Models
class SubscriptionBase(BaseModel):
    user_id: int
    plan_type: str
    end_date: datetime
    amount: float
    auto_renew: Optional[bool] = True

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    subscription_id: int
    start_date: datetime
    is_active: bool
    stripe_subscription_id: Optional[str]
    canceled_at: Optional[datetime]

    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    user_id: int
    subscription_id: int
    amount: float
    payment_method: str

class TransactionCreate(TransactionBase):
    stripe_payment_intent_id: Optional[str]
    transaction_metadata: Optional[str]

class TransactionResponse(TransactionBase):
    transaction_id: int
    status: str
    created_at: datetime
    stripe_payment_intent_id: Optional[str]
    refund_for_transaction_id: Optional[int]

    class Config:
        from_attributes = True

class PaymentIntentCreate(BaseModel):
    amount: float
    currency: str = "usd"
    payment_method_types: list[str] = ["card"]
    metadata: Optional[dict]

class RefundCreate(BaseModel):
    transaction_id: int
    reason: Optional[str]