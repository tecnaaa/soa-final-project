"""
SQLAlchemy models for the User service.

Defines the 'Role' and 'User' tables, and includes password
hashing and verification logic within the User model.
"""

# --- 1. Imports ---

# Standard Library
import sys
from pathlib import Path

# Third-Party Imports
from passlib.context import CryptContext
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Numeric, TIMESTAMP, 
    Enum as SQLEnum
)
from sqlalchemy.sql import func

# --- 2. Path Setup (for local imports) ---

# Thêm thư mục backend vào Python path để import
# (Cần thiết để chạy 'main.py' trực tiếp)
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# --- 3. Local Application Imports ---

try:
    from db.db import Base
except ImportError:
    print(f"Lỗi: Không thể import 'Base' từ db.db. Đã tìm trong: {backend_dir}")
    sys.exit(1)

# --- 4. Password Hashing Setup ---

# Cấu hình context (ngữ cảnh) hash mật khẩu
# Được định nghĩa 1 lần và tái sử dụng trong model 'User'
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- 5. Model Definitions ---

class Role(Base):
    """
    SQLAlchemy model cho bảng 'roles'.
    Đại diện cho các vai trò (User, PT, Admin).
    """
    __tablename__ = 'roles'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(
        SQLEnum('User', 'PT', 'Admin', name='role_enum', native_enum=False), 
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
        SQLEnum('Nam', 'Nữ', 'Khác', name='gender_enum', native_enum=False)
    )
    height_cm = Column(Numeric(5, 2))
    weight_kg = Column(Numeric(5, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # --- Phương thức xử lý mật khẩu ---

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash một mật khẩu gốc để lưu trữ."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """So sánh mật khẩu gốc với hash đã lưu trong DB."""
        return pwd_context.verify(plain_password, self.password_hash)