"""
Database connection (async) for all services.
PHIÊN BẢN SỬA LỖI: Logic URL an toàn và dọn dẹp import/export.
"""
import os
import logging
from typing import AsyncGenerator
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# --- Database Configuration ---
RAW_DATABASE_URL = os.getenv("DATABASE_URL")
if not RAW_DATABASE_URL:
    logger.error("No database URL configured. Please set DATABASE_URL in .env file")
    raise ValueError("No database URL configured. Please set DATABASE_URL in .env file")

# --- SỬA LỖI LOGIC: Chuyển đổi URL sang +asyncmy một cách an toàn ---
if RAW_DATABASE_URL.startswith("mysql+pymysql://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL.replace("mysql+pymysql://", "mysql+asyncmy://")
elif RAW_DATABASE_URL.startswith("mysql+aiomysql://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL.replace("mysql+aiomysql://", "mysql+asyncmy://")
elif RAW_DATABASE_URL.startswith("mysql://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL.replace("mysql://", "mysql+asyncmy://")
elif RAW_DATABASE_URL.startswith("mysql+asyncmy://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL # Nó đã đúng
else:
    logger.error(f"DATABASE_URL không nhận dạng được: {RAW_DATABASE_URL}")
    raise ValueError("DATABASE_URL format not recognized for async conversion")

try:
    # Log phiên bản đã ẩn thông tin
    sanitized_url = ASYNC_DATABASE_URL.split('@', 1)[-1]
    logger.info(f"Connecting to database: mysql+asyncmy://...@{sanitized_url}")
except Exception:
    logger.info("Connecting to database...")


# --- SQLAlchemy Engine and Session Setup (Chỉ ASYNC) ---
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False # Quan trọng cho async
)

Base = declarative_base()

# --- FastAPI Dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency: Tạo và cung cấp một session database async.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except HTTPException:
            await session.rollback()
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error during session: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error occurred: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error(f"An unexpected error occurred during session: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

# --- Utility Function ---
async def init_db():
    pass

async def init_default_admin():
    """
    (Async) Tạo tài khoản admin mặc định nếu chưa tồn tại.
    """
    try:
        from models.user.user_models import User, Role
        
        async with AsyncSessionLocal() as db:
            try:
                # Kiểm tra admin
                result = await db.execute(select(User).filter(User.email == "admin@app.com"))
                admin_user = result.scalars().first()
                
                if admin_user:
                    logger.info("✅ Tài khoản admin đã tồn tại")
                    return
                
                # Kiểm tra role
                role_result = await db.execute(select(Role).filter(Role.role_name == "Admin"))
                admin_role = role_result.scalars().first()
                
                if not admin_role:
                    logger.info("Tạo role Admin...")
                    admin_role = Role(role_name="Admin", description="Administrator role")
                    db.add(admin_role)
                    await db.commit()
                    await db.refresh(admin_role)
                    logger.info("✅ Tạo role Admin thành công")
                
                logger.info("Tạo tài khoản admin...")
                admin_user = User(
                    email="admin@app.com",
                    password_hash=User.hash_password("11111111"),
                    first_name="Admin",
                    last_name="User",
                    role_id=admin_role.role_id,
                    gender="Khác"
                )
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                
                logger.info(f"✅ Tạo tài khoản admin thành công!")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Lỗi khi tạo tài khoản admin: {str(e)}", exc_info=True)
                
    except ImportError as e:
        logger.error(f"❌ Lỗi import models khi tạo admin: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định khi tạo admin: {str(e)}", exc_info=True)