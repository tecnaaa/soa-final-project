"""
Unit tests for User Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.users.main import app, get_db
from db.db import Base
from models.user.user_models import User, Role

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
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

class TestUserRegistration:
    """Test cases for user registration"""
    
    def test_register_new_user(self, setup_teardown):
        """Test successful user registration"""
        response = client.post(
            "/register",
            json={
                "email": "testuser@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "SecurePassword123!",
                "gender": "Nam",
                "height_cm": 175,
                "weight_kg": 70
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["first_name"] == "Test"
        assert "password" not in data

    def test_register_duplicate_email(self, setup_teardown):
        """Test registration with duplicate email"""
        # Register first user
        client.post(
            "/register",
            json={
                "email": "duplicate@example.com",
                "first_name": "First",
                "last_name": "User",
                "password": "SecurePassword123!"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/register",
            json={
                "email": "duplicate@example.com",
                "first_name": "Second",
                "last_name": "User",
                "password": "SecurePassword123!"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self, setup_teardown):
        """Test registration with weak password"""
        response = client.post(
            "/register",
            json={
                "email": "weakpass@example.com",
                "first_name": "Weak",
                "last_name": "Pass",
                "password": "123"  # Too weak
            }
        )
        assert response.status_code == 400

    def test_register_invalid_email(self, setup_teardown):
        """Test registration with invalid email"""
        response = client.post(
            "/register",
            json={
                "email": "invalid-email",
                "first_name": "Invalid",
                "last_name": "Email",
                "password": "SecurePassword123!"
            }
        )
        assert response.status_code == 422  # Validation error

class TestUserLogin:
    """Test cases for user login"""
    
    def test_login_success(self, setup_teardown):
        """Test successful login"""
        # Create user first
        client.post(
            "/register",
            json={
                "email": "logintest@example.com",
                "first_name": "Login",
                "last_name": "Test",
                "password": "SecurePassword123!"
            }
        )
        
        # Try login
        response = client.post(
            "/token",
            data={
                "username": "logintest@example.com",
                "password": "SecurePassword123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, setup_teardown):
        """Test login with wrong password"""
        # Create user
        client.post(
            "/register",
            json={
                "email": "wrongpass@example.com",
                "first_name": "Wrong",
                "last_name": "Pass",
                "password": "CorrectPassword123!"
            }
        )
        
        # Try login with wrong password
        response = client.post(
            "/token",
            data={
                "username": "wrongpass@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, setup_teardown):
        """Test login with non-existent user"""
        response = client.post(
            "/token",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        assert response.status_code == 401

class TestUserProfile:
    """Test cases for user profile operations"""
    
    def test_get_current_user_profile(self, setup_teardown):
        """Test getting current user profile"""
        # Register and login
        client.post(
            "/register",
            json={
                "email": "profile@example.com",
                "first_name": "Profile",
                "last_name": "Test",
                "password": "SecurePassword123!"
            }
        )
        
        login_response = client.post(
            "/token",
            data={
                "username": "profile@example.com",
                "password": "SecurePassword123!"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get profile
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"

    def test_update_user_profile(self, setup_teardown):
        """Test updating user profile"""
        # Register and login
        client.post(
            "/register",
            json={
                "email": "update@example.com",
                "first_name": "Update",
                "last_name": "Test",
                "password": "SecurePassword123!",
                "height_cm": 170,
                "weight_kg": 65
            }
        )
        
        login_response = client.post(
            "/token",
            data={
                "username": "update@example.com",
                "password": "SecurePassword123!"
            }
        )
        token = login_response.json()["access_token"]
        
        # Update profile
        response = client.put(
            "/users/me",
            json={
                "email": "update@example.com",
                "first_name": "Updated",
                "last_name": "Name",
                "password": "",
                "height_cm": 180,
                "weight_kg": 75
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["height_cm"] == 180

    def test_get_profile_without_token(self, setup_teardown):
        """Test getting profile without authentication token"""
        response = client.get("/users/me")
        assert response.status_code == 403

class TestPasswordHashing:
    """Test cases for password hashing and verification"""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        plain_password = "TestPassword123!"
        hashed = User.hash_password(plain_password)
        
        # Hash should not equal plain password
        assert hashed != plain_password
        # Hash should be reproducible
        assert User.hash_password(plain_password) != hashed  # Different salt

    def test_password_verification(self):
        """Test password verification"""
        plain_password = "TestPassword123!"
        user = User(
            email="test@example.com",
            password_hash=User.hash_password(plain_password),
            first_name="Test",
            last_name="User",
            role_id=1
        )
        
        # Correct password should verify
        assert user.verify_password(plain_password) is True
        # Wrong password should not verify
        assert user.verify_password("WrongPassword123!") is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
