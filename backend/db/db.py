"""
Database connection (async) for Users service.

This module handles:
1. Loading the database URL from environment variables.
2. Creating the async SQLAlchemy engine and session factory.
3. Providing a FastAPI dependency 'get_db' for sessions.
4. Providing a helper 'init_db' to create tables on startup.
"""

# --- 1. Imports ---
# Sắp xếp theo: Thư viện chuẩn, Thư viện bên thứ ba

# Standard Library
import os
import logging
from typing import AsyncGenerator  # Thêm vào để type-hint 'get_db' rõ hơn

# Third-Party
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# --- 2. Setup (Logging and Environment) ---

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- 3. Database Configuration ---

DATABASE_URL = os.getenv("USERS_DATABASE_URL") or os.getenv("USERS_DATABASE")
if not DATABASE_URL:
    logger.error("No database URL configured. Please set USERS_DATABASE_URL in .env file")
    raise ValueError("No database URL configured. Please set USERS_DATABASE_URL in .env file")

# Log a sanitized version of the URL for security
logger.info(f"Connecting to database: {DATABASE_URL.replace('mysql+aiomysql://', 'mysql://')}")

# --- 4. SQLAlchemy Engine and Session Setup ---

# Create async engine with connection pool settings
engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # Tắt log SQL, chỉ bật khi debug
    future=True,          # Sử dụng API 2.0 của SQLAlchemy
    pool_pre_ping=True,   # Kiểm tra kết nối trước khi sử dụng từ pool
    pool_size=5,          # Số lượng kết nối tối đa trong pool
    max_overflow=10       # Số kết nối có thể tạo vượt pool_size khi cần
)

# Async session factory, đây là "nhà máy" tạo ra các session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Cần thiết cho FastAPI
)

# Base class cho tất cả các model (trong file models.py sẽ kế thừa từ đây)
Base = declarative_base()

# --- 5. FastAPI Dependency ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency: Tạo và cung cấp một session database.
    Đảm bảo session được đóng lại (kể cả khi có lỗi).
    """
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during session: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"An unexpected error occurred during session: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# --- 6. Utility Function ---

async def init_db():
    """
    Hàm helper để tạo tất cả các bảng trong DB.
    Thường được gọi 1 lần khi server startup.
    """
    async with engine.begin() as conn:
        # 'run_sync' cho phép chạy code sync (create_all) trong môi trường async
        await conn.run_sync(Base.metadata.create_all)