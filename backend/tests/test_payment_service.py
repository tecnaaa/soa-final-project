"""
Unit tests for Payment Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.payment.main import app, get_db
from db.db import Base
from models.payment.payment_models import Subscription, Transaction

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_payment.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def setup_teardown():
    """Fixture to setup and teardown test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestSubscriptionManagement:
    """Test cases for subscription management"""
    
    def test_get_subscription_plans(self, setup_teardown):
        """Test retrieving available subscription plans"""
        response = client.get("/subscription-plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) >= 3
        
        # Check free plan exists
        free_plan = next((p for p in data["plans"] if p["type"] == "free"), None)
        assert free_plan is not None
        assert free_plan["price"] == 0

    def test_create_subscription(self, setup_teardown):
        """Test creating a new subscription"""
        response = client.post(
            "/subscriptions/",
            json={
                "user_id": 1,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_type"] == "premium"
        assert data["amount"] == 9.99
        assert data["is_active"] == True

    def test_get_active_subscription(self, setup_teardown):
        """Test retrieving active subscription for user"""
        # Create subscription first
        client.post(
            "/subscriptions/",
            json={
                "user_id": 1,
                "plan_type": "coaching",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 49.99
            }
        )
        
        response = client.get("/subscriptions/user/1")
        assert response.status_code == 200
        data = response.json()
        assert data["plan_type"] == "coaching"

    def test_cancel_subscription(self, setup_teardown):
        """Test cancelling a subscription"""
        # Create subscription
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 2,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        sub_id = sub_response.json()["subscription_id"]
        
        # Cancel subscription
        response = client.delete(f"/subscriptions/{sub_id}")
        assert response.status_code == 200

    def test_upgrade_subscription(self, setup_teardown):
        """Test upgrading subscription plan"""
        # Create free subscription
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 3,
                "plan_type": "free",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 0
            }
        )
        
        # Upgrade to premium
        upgrade_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 3,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        assert upgrade_response.status_code == 200

class TestTransactionManagement:
    """Test cases for transaction management"""
    
    def test_create_transaction(self, setup_teardown):
        """Test creating a new transaction"""
        # Create subscription first
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 1,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        sub_id = sub_response.json()["subscription_id"]
        
        # Create transaction
        response = client.post(
            "/transactions/",
            json={
                "user_id": 1,
                "subscription_id": sub_id,
                "amount": 9.99,
                "payment_method": "credit_card"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 9.99
        assert data["status"] == "completed"

    def test_get_user_transactions(self, setup_teardown):
        """Test retrieving user transactions"""
        # Create subscription and transaction
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 2,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        sub_id = sub_response.json()["subscription_id"]
        
        client.post(
            "/transactions/",
            json={
                "user_id": 2,
                "subscription_id": sub_id,
                "amount": 9.99,
                "payment_method": "credit_card"
            }
        )
        
        response = client.get("/transactions/user/2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_transaction_details(self, setup_teardown):
        """Test retrieving specific transaction details"""
        # Create subscription and transaction
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 3,
                "plan_type": "coaching",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 49.99
            }
        )
        sub_id = sub_response.json()["subscription_id"]
        
        trans_response = client.post(
            "/transactions/",
            json={
                "user_id": 3,
                "subscription_id": sub_id,
                "amount": 49.99,
                "payment_method": "credit_card"
            }
        )
        trans_id = trans_response.json()["transaction_id"]
        
        response = client.get(f"/transactions/{trans_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == trans_id

class TestPaymentIntegration:
    """Test cases for payment gateway integration"""
    
    def test_subscription_plans_have_prices(self, setup_teardown):
        """Test that subscription plans have correct pricing"""
        response = client.get("/subscription-plans")
        data = response.json()
        plans = data["plans"]
        
        # Verify pricing
        free_plan = next(p for p in plans if p["type"] == "free")
        premium_plan = next(p for p in plans if p["type"] == "premium")
        coaching_plan = next(p for p in plans if p["type"] == "coaching")
        
        assert free_plan["price"] == 0
        assert premium_plan["price"] == 9.99
        assert coaching_plan["price"] == 49.99

    def test_transaction_status_flow(self, setup_teardown):
        """Test transaction status transitions"""
        # Create subscription
        sub_response = client.post(
            "/subscriptions/",
            json={
                "user_id": 4,
                "plan_type": "premium",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 9.99
            }
        )
        sub_id = sub_response.json()["subscription_id"]
        
        # Create transaction
        trans_response = client.post(
            "/transactions/",
            json={
                "user_id": 4,
                "subscription_id": sub_id,
                "amount": 9.99,
                "payment_method": "credit_card"
            }
        )
        
        assert trans_response.status_code == 200
        data = trans_response.json()
        assert data["status"] in ["pending", "completed", "failed"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
