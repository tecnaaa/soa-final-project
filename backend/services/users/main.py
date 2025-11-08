"""
Users service (API + MySQL connection)

Handles user-related operations, connecting to a MySQL `user_db` via
async SQLAlchemy.
"""

# --- 1. Imports ---

# Standard Library
import logging
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal

# Third-Party Imports
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic.utils import GetterDict
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# --- 2. Local/Application Imports ---

# Add backend directory to Python path for imports
import sys
import os
from pathlib import Path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from models.user.user_models import User, Role
from db.db import get_db, init_db

# --- 3. Pydantic Models (Data Schema) ---

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

class UserCreate(UserBase):
    """Pydantic model for creating a new user (includes password)."""
    password: str  # For creating user, we need password

class UserOut(UserBase):
    """Pydantic model for API responses (excludes password)."""
    user_id: int
    created_at: Optional[datetime] = None

# --- 4. FastAPI Application Setup ---

app = FastAPI(title="Users Service")

# --- 5. Application Events ---

@app.on_event("startup")
async def on_startup():
    """
    Initialize the database on application startup.
    Creates tables defined in models_db.py if they don't exist.
    """
    try:
        await init_db()
        logging.info("Database tables initialized.")
    except Exception as e:
        # Log the error but allow the app to continue running
        # The DB might be down, or tables already exist, etc.
        logging.warning(f"Database initialization failed: {e}")
        pass

# --- 6. API Endpoints ---

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
        logging.exception("DB query failed for list_users_db")
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


@app.post("/users", response_model=UserOut)
async def create_user_db(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user in the database.
    
    WARNING: This is a minimal example. Passwords MUST be hashed in production.
    """
    # Check if user already exists
    try:
        q = select(User).where(User.email == payload.email)
        res = await db.execute(q)
        existing = res.scalars().first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        # --- DANGER: HASH PASSWORD IN PRODUCTION ---
        # This is insecure and only for development.
        # Use libraries like 'passlib' and 'bcrypt'.
        # Example: hashed_password = pwd_context.hash(payload.password)
        hashed_password = payload.password  # <--- REPLACE THIS
        # ------------------------------------------

        new_user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            role_id=payload.role_id,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            password_hash=hashed_password # Store the HASHED password
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # orm_mode=True in UserOut will handle the conversion
        return new_user
        
    except HTTPException as http_ex:
        # Re-raise known HTTP exceptions (like the 400)
        raise http_ex
    except Exception as e:
        logging.exception("DB write failed for create_user_db")
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

# --- 7. Main entry point (for direct execution) ---

if __name__ == "__main__":
    import uvicorn
    logging.info("Starting Users Service directly...")
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)