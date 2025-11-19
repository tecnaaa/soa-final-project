"""
SQLAlchemy models for the User service.

Defines the 'Role' and 'User' tables, and includes password
hashing and verification logic within the User model.
"""

# --- 1. Imports ---

# Standard Library
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Third-Party Imports
from passlib.context import CryptContext
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Numeric, TIMESTAMP, 
    Enum as SQLEnum
)
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, field_validator
from pydantic.config import ConfigDict

# --- 2. Path Setup (for local imports) ---

# Thêm thư mục backend vào Python path để import
# (Cần thiết để chạy 'main.py' trực tiếp)
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# --- 3. Local Application Imports ---

try:
    # Import Base từ db module
    from db import Base
except ImportError:
    print(f"Lỗi: Không thể import 'Base' từ db module. Đã tìm trong: {backend_dir}")
    sys.exit(1)

# --- 4. Password Hashing Setup ---

# Cấu hình context (ngữ cảnh) hash mật khẩu
# Được định nghĩa 1 lần và tái sử dụng trong model 'User'
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- 5. Model Definitions ---

class Role(Base):
    """
    SQLAlchemy model cho bảng 'roles'.
    Đại diện cho các vai trò (user, pt, admin).
    """
    __tablename__ = 'roles'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(
        SQLEnum('user', 'pt', 'admin', name='role_enum', native_enum=False), 
        nullable=False
    )


class User(Base):
    """
    SQLAlchemy model cho bảng 'users'.
    Lưu trữ thông tin người dùng và xử lý logic mật khẩu.
    """
    __tablename__ = 'users'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    user_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    gender = Column(
        SQLEnum('nam', 'nu', 'khac', name='gender_enum', native_enum=False)
    )
    height_cm = Column(Numeric(5, 2))
    weight_kg = Column(Numeric(5, 2))
    avatar_url = Column(String(255), nullable=True)  # Lưu đường dẫn avatar
    created_at = Column(TIMESTAMP, server_default=func.now())

    # --- Phương thức xử lý mật khẩu ---

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash một mật khẩu gốc để lưu trữ."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """So sánh mật khẩu gốc với hash đã lưu trong DB."""
        return pwd_context.verify(plain_password, self.password_hash)


# --- 6. Pydantic Models ---

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str
    role_id: int = 1  # Default to normal user

class UserInDB(UserBase):
    user_id: int
    role_id: int
    password_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    user_id: int
    role_id: int
    created_at: datetime
    avatar_url: Optional[str] = None # Thêm trường này vào response

    model_config = ConfigDict(from_attributes=True)

    @field_validator('avatar_url', mode='before')
    @classmethod
    def set_default_avatar(cls, v):
        """
        Nếu avatar_url trong DB là None hoặc Rỗng, trả về đường dẫn mặc định.
        Logic này đảm bảo Frontend luôn nhận được một đường dẫn ảnh hợp lệ.
        """
        if not v:
            # Trả về đường dẫn API đến ảnh mặc định
            # Frontend sẽ gọi: http://localhost:8001/files/uploads/default.webp
            return "/files/uploads/default.webp"
        return v