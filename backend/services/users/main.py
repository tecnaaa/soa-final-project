"""
Users service (API + MySQL connection)

Handles user-related operations, connecting to a MySQL `user_db` via
async SQLAlchemy.
"""

# --- 1. Imports ---

# Standard Library
import logging
import sys
import os
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Third-Party Imports
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic.utils import GetterDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# --- 2. Logging Setup ---

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('users_service.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)


# --- 3. Local/Application Imports ---

# Add backend directory to Python path for imports
# (Điều này cần thiết để chạy file main.py trực tiếp)
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from models.user.user_models import User, Role
    from db.db import get_db, init_db
except ImportError:
    logger.critical("Import Error: Không thể tìm thấy 'models' hoặc 'db'.")
    logger.critical(f"Đang tìm trong: {backend_dir}")
    sys.exit(1)


# --- 4. Pydantic Models (Data Schema) ---

class SQLAlchemyUserGetter(GetterDict):
    """
    Custom GetterDict to handle special data types like Decimal
    when converting from SQLAlchemy model to Pydantic model.
    """
    def get(self, key: str, default: Any = None) -> Any:
        # Handle SQLAlchemy model attribute access
        if key in {'height_cm', 'weight_kg'} and hasattr(self._obj, key):
            val = getattr(self._obj, key)
            if val is not None:
                # Ensure Decimal is converted from string for precision
                return Decimal(str(val))
            return None
        return super().get(key, default)

class UserBase(BaseModel):
    """Base Pydantic model for a User."""
    email: str
    first_name: str
    last_name: str
    role_id: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None

    class Config:
        orm_mode = True
        getter_dict = SQLAlchemyUserGetter

class UserRegister(UserBase):
    """Pydantic model for user registration."""
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    """Pydantic model for user login."""
    email: str
    password: str

class UserCreate(UserBase):
    """Pydantic model for creating a user (includes password)."""
    password: str

class UserOut(UserBase):
    """Pydantic model for API responses (excludes password)."""
    user_id: int
    created_at: Optional[datetime] = None

class LoginResponse(BaseModel):
    """Pydantic model for login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- 5. FastAPI Application Setup ---

app = FastAPI(title="Users Service")


@app.on_event("startup")
async def on_startup():
    """
    Initialize the database on application startup.
    Creates tables defined in models_db.py if they don't exist.
    """
    try:
        await init_db()
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}", exc_info=True)
        pass


# --- 6. API Endpoints ---

# REGISTER METHOD
@app.post("/register", response_model=UserOut)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    logger.info(f"Attempting to register user with email: {user_data.email}")
    try:
        # Validate passwords match
        if user_data.password != user_data.confirm_password:
            logger.warning(f"Password mismatch for email: {user_data.email}")
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Check if email exists
        query = select(User).where(User.email == user_data.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Email already exists: {user_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        logger.info(f"Creating new user for email: {user_data.email}")
        
        # Create new user (default role_id=1 for normal user)
        hashed_password = User.hash_password(user_data.password)
        logger.debug("Password hashed successfully")

        # SỬA LỖI: Nếu gender là chuỗi rỗng, đổi nó thành None (NULL)
        user_gender = user_data.gender if user_data.gender else None

        new_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=hashed_password,
            role_id=user_data.role_id or 1,  # Default to normal user role
            gender=user_gender, # <--- Đã sửa
            height_cm=user_data.height_cm,
            weight_kg=user_data.weight_kg
        )
        
        logger.debug("Attempting to add user to database")
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Successfully registered user: {user_data.email}")
        return UserOut.from_orm(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Registration failed. Please contact support. Error: {str(e)}"
        )

# LOGIN METHOD
@app.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return access token.
    """
    logger.info(f"Login attempt for email: {credentials.email}")
    try:
        # Find user by email
        query = select(User).where(User.email == credentials.email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        # Kiểm tra user và mật khẩu
        if not user or not user.verify_password(credentials.password):
            logger.warning(f"Invalid email or password for: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"Successful login for user: {credentials.email}")
        
        # --- ⚠️ CẢNH BÁO: TOKEN KHÔNG AN TOÀN ---
        # Đây là token giả (dummy) chỉ để phát triển.
        # Trong production, hãy sử dụng JWT (JSON Web Token) thực sự.
        access_token = f"dummy-token-for-{user.user_id}-{datetime.utcnow().timestamp()}"
        # ------------------------------------
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserOut.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {credentials.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Login failed. Please contact support. Error: {str(e)}"
        )

# List all users in DB
@app.get("/users", response_model=List[UserOut])
async def list_users_db(db: AsyncSession = Depends(get_db)):
    """
    Return a list of all users from the database.
    """
    try:
        result = await db.execute(
            select(User)
            .order_by(User.user_id)
        )
        users = result.scalars().all()
        
        # Use from_orm for explicit conversion
        return [UserOut.from_orm(user) for user in users]
    
    except Exception as e:
        logger.exception("DB query failed for list_users_db", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    
# --- 7. Main entry point (for direct execution) ---

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Users Service directly...")
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)