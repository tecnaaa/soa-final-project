"""
Users service (API + MySQL connection)
"""

# --- 1. Setup Python Path TRƯỚC (Quan trọng!) ---
import sys
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = str(Path(__file__).parent.parent.parent)
if (backend_dir not in sys.path):
    sys.path.insert(0, backend_dir)

# --- 2. Imports ---
import os
from fastapi import FastAPI, HTTPException, Depends, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
# THÊM: Import 'select' và 'text' cho truy vấn async
from sqlalchemy import select, text
from datetime import datetime, timedelta
import logging
from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator
from jose import JWTError, jwt
from dotenv import load_dotenv
from pydantic import model_validator
import redis.asyncio as redis

# --- 3. BƯỚC NÀY: Import các module backend (sau khi sys.path đã được setup) ---
try:
    from models.user.user_models import User, UserResponse
    from db.db import get_db, init_db
    from services.auth_middleware import setup_auth_logging, track_auth_activity
    from services.security_utils import SecurityUtils
    from services.security_middleware import SecurityMiddleware
    from services.error_tracking import init_error_tracking, capture_error
    from services.file_upload import save_upload_file, delete_file, get_file_url, get_file
    from services.email_service import email_service
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# --- 4. Configuration and Setup ---

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "a_default_secret_key_for_development"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security setup
security_utils = SecurityUtils()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Users Service")

# Thêm security middleware
app.middleware('http')(SecurityMiddleware())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('users_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize error tracking
init_error_tracking("users_service")

# Thiết lập logging
setup_auth_logging(app)

# --- 3. Pydantic Models (Data Schema) ---
# (Không cần thay đổi các Pydantic model)

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    role_id: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

class UserRegister(UserBase):
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    """Model cho update user info - không yêu cầu email và password bắt buộc"""
    first_name: str
    last_name: str
    gender: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('gender', mode='before')
    @classmethod
    def convert_empty_gender(cls, v):
        """Convert empty string to None ONLY for gender (which is nullable)"""
        if v == '':
            return None
        return v

class UserOut(UserBase):
    user_id: int
    created_at: Optional[datetime] = None

class LoginResponse(BaseModel):
    """Model cho login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLoginRequest(BaseModel):
    """Model cho login request từ frontend"""
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    """Model cho refresh token request"""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Model cho yêu cầu đặt lại mật khẩu"""
    email: str

class PasswordResetConfirm(BaseModel):
    """Model cho xác nhận đặt lại mật khẩu"""
    token: str
    new_password: Optional[str] = None
    newPassword: Optional[str] = None # Thêm trường này để bắt dữ liệu cũ từ frontend

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='before')
    @classmethod
    def consolidate_password(cls, data: Any) -> Any:
        """
        Tự động chuyển đổi newPassword (frontend cũ) thành new_password (backend chuẩn)
        """
        if isinstance(data, dict):
            # Nếu có newPassword mà thiếu new_password, hãy copy sang
            if 'newPassword' in data and not data.get('new_password'):
                data['new_password'] = data['newPassword']
        return data
    
    @field_validator('new_password')
    def validate_password_not_empty(cls, v):
        if not v:
            raise ValueError('Mật khẩu không được để trống')
        return v

# --- 4. Helper Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Creates a new JWT refresh token - valid for 7 days"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# BƯỚC A.1: HÀM MỚI (chỉ giải mã token)
async def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return TokenData(email=email) # Chỉ trả về email
    except JWTError:
        raise credentials_exception

# BƯỚC A.2: THAY THẾ HÀM CŨ BẰNG HÀM NÀY
async def get_current_user(
    token_data: TokenData = Depends(get_token_data),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Lấy user từ DB, sử dụng session DB của endpoint gọi nó.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found from token"
    )
    
    try:
        result = await db.execute(select(User).where(User.email == token_data.email))
        user = result.scalars().first()
        
        if user is None:
            raise credentials_exception
        
        # Sửa dữ liệu 'gender' rỗng nếu có (để xử lý data hỏng)
        if user.gender == '':
            logger.warning(f"Fixing empty gender for user {user.email}")
            user.gender = None
        
        return user
    except Exception as e:
        logger.error(f"Error loading user {token_data.email} in get_current_user: {str(e)}")
        # Ném lỗi 401 nếu có bất kỳ lỗi nào khi đọc user (kể cả lỗi enum)
        raise credentials_exception

# --- 5. Authentication Functions ---

async def authenticate_user(email: str, password: str, db: AsyncSession, request: Request) -> Optional[User]: # SỬA: AsyncSession
    """Xác thực người dùng"""
    client_ip = request.client.host
    
    try:
        # Kiểm tra tài khoản có bị khóa không
        is_locked, remaining_time = security_utils.is_account_locked(email)
        if is_locked:
            logger.warning(f"Account locked for {email} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked. Try again in {remaining_time.seconds // 60} minutes"
            )
    except AttributeError:
        # security_utils không có method này, bỏ qua
        pass

    # Tìm user
    # SỬA: Chuyển sang cú pháp async với .where()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user or not user.verify_password(password):
        try:
            security_utils.track_failed_attempt(email)
        except AttributeError:
            pass
        logger.warning(f"Failed login attempt for {email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user.gender == '':
        user.gender = None

    # Xóa lịch sử đăng nhập thất bại nếu thành công
    try:
        security_utils.clear_failed_attempts(email)
    except AttributeError:
        pass
    logger.info(f"Successful login for {email} from {client_ip}")
    return user

# --- 6. API Endpoints ---

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)): # SỬA: get_db
    """
    Health check endpoint that verifies database connectivity.
    """
    try:
        # Thực hiện một truy vấn đơn giản để kiểm tra kết nối DB
        await db.execute(text("SELECT 1")) # SỬA: await
        logger.info("Health check: Database connection is healthy.")
        return {"status": "healthy", "service": "users", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available"
        )

@app.get("/debug/email-config")
async def debug_email_config():
    """
    Debug endpoint - Kiểm tra cấu hình email SMTP
    """
    try:
        from services.email_service import email_service
        import os
        
        return {
            "smtp_host": email_service.smtp_host,
            "smtp_port": email_service.smtp_port,
            "smtp_user": email_service.smtp_user if email_service.smtp_user else "(NOT SET)",
            "smtp_password": "***" if email_service.smtp_password else "(NOT SET)",
            "sender_email": email_service.sender_email,
            "sender_name": email_service.sender_name,
            "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
            "status": "✅ Email service is configured" if (email_service.smtp_user and email_service.smtp_password) else "❌ Email service NOT configured"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "❌ Error checking email config"
        }

@app.post("/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint đăng nhập"""
    user = await authenticate_user(form_data.username, form_data.password, db, request)
    
    # Tạo access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role_id},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Token generated for user {user.user_id}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@app.post("/login", response_model=LoginResponse)
async def login_json(
    request: Request,
    user_login: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Endpoint đăng nhập nhận JSON body"""
    user = await authenticate_user(user_login.username, user_login.password, db, request)
    
    # Tạo access token và refresh token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role_id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role_id})
    
    # Chuyển UserResponse thành dict
    user_response = UserResponse.from_orm(user)
    user_dict = user_response.model_dump()
    
    logger.info(f"Token generated for user {user.user_id}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_dict
    }

@app.post("/auth/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db) # SỬA: get_db
):
    """Endpoint refresh token"""
    try:
        payload = jwt.decode(refresh_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # SỬA: Chuyển sang cú pháp async với .where()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Tạo access token mới
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role_id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role_id})
    
    # Chuyển UserResponse thành dict
    user_response = UserResponse.from_orm(user)
    user_dict = user_response.model_dump()
    
    logger.info(f"Token refreshed for user {user.user_id}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_dict
    }

@app.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db) # SỬA: get_db
):
    """Đăng ký"""
    client_ip = request.client.host
    
    try:
        # Kiểm tra độ mạnh mật khẩu
        is_strong, error_message = security_utils.check_password_strength(user_data.password)
        if not is_strong:
            logger.warning(f"Weak password attempt from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except AttributeError:
        # Nếu không có method check_password_strength, skip validation
        pass

    # Kiểm tra email đã tồn tại
    # SỬA: Chuyển sang cú pháp async với .where()
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        logger.warning(f"Registration attempt with existing email {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        new_user = User(
            email=user_data.email,
            password_hash=User.hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_id=user_data.role_id or 1,
            gender=user_data.gender,
            height_cm=user_data.height_cm,
            weight_kg=user_data.weight_kg
        )
        db.add(new_user)
        await db.commit()   # SỬA: await
        await db.refresh(new_user) # SỬA: await
        
        logger.info(f"User registered: {new_user.user_id}")
        
        return UserResponse.from_orm(new_user)
    except Exception as e:
        await db.rollback() # SỬA: await
        logger.error(f"Error creating user: {str(e)}")
        capture_error(e, {"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    track_auth_activity(current_user.user_id, "profile_access", "success")
    return current_user

@app.put("/users/me", response_model=UserResponse)
async def update_user(
    request: Request,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db) # db session được cung cấp bởi get_db
):
    """Cập nhật thông tin user"""
    client_ip = request.client.host
    
    try:
        if user_update.password:
            # (Logic kiểm tra độ mạnh mật khẩu...)
            current_user.password_hash = User.hash_password(user_update.password)
            logger.info(f"Password changed for user {current_user.user_id}")

        # Cập nhật các thông tin khác
        current_user.first_name = user_update.first_name
        current_user.last_name = user_update.last_name
        
        # LOGIC SỬA LỖI:
        # Chỉ cập nhật 'gender' nếu nó được cung cấp (không phải None)
        if user_update.gender is not None:
            if user_update.gender in ('nam', 'nu', 'khac'):
                current_user.gender = user_update.gender
            else:
                # Nếu frontend gửi '' hoặc giá trị không hợp lệ
                logger.warning(f"Giá trị gender không hợp lệ '{user_update.gender}' nhận được, gán mặc định là 'Khác'.")
                current_user.gender = 'khac'
        
        # Nếu user_update.gender là None, không làm gì cả (giữ nguyên giá trị cũ trong DB)
            
        current_user.height_cm = user_update.height_cm
        current_user.weight_kg = user_update.weight_kg
        
        # XÓA: `await db.commit()` và `await db.refresh(current_user)`
        # `get_db` sẽ tự động commit khi kết thúc hàm này.
        
        logger.info(f"User profile updated: {current_user.user_id}")
        
        return current_user
        
    except Exception as e:
        # XÓA: `await db.rollback()`
        # `get_db` sẽ tự động rollback nếu có Exception
        
        logger.error(f"Error updating user: {str(e)}")
        capture_error(e, {"user_id": current_user.user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

@app.post("/users/me/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload profile image, delete old one, and update DB"""
    try:
        # 1. Lưu file mới (Hàm này đã bao gồm logic xóa file cũ của user_id này)
        # Kết quả trả về ví dụ: "uploads/1.png"
        relative_path = await save_upload_file(file, current_user.user_id)
        
        # 2. Tạo URL để Frontend truy cập (ví dụ: /files/1.png)
        file_url_api = get_file_url(relative_path)
        
        # 3. Cập nhật vào Database (Lưu URL API để frontend dễ dùng)
        current_user.avatar_url = file_url_api
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"Profile image updated for user {current_user.user_id}: {relative_path}")
        
        return {
            "message": "Profile image uploaded successfully",
            "file_path": relative_path,
            "file_url": file_url_api,
            "user": UserResponse.from_orm(current_user)
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading profile image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading profile image: {str(e)}"
        )

# Tìm đoạn @app.get("/files/{file_path:path}") và sửa thành:

@app.get("/files/{file_path:path}")
async def get_file_endpoint(file_path: str):
    """
    Serve static files (images)
    """
    try:
        return await get_file(file_path)
    except HTTPException:
        # Cho phép lỗi 404 từ get_file đi qua, không bị bắt bởi Exception chung
        raise
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving file"
        )

@app.delete("/users/me/delete-profile-image/{image_id}")
async def delete_profile_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db) # SỬA: get_db
):
    """Delete profile image for current user"""
    try:
        file_path = f"uploads/{current_user.user_id}/profile/{image_id}"
        success = await delete_file(file_path)
        
        if success:
            logger.info(f"Profile image deleted for user {current_user.user_id}")
            return {"message": "Profile image deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
    except Exception as e:
        logger.error(f"Error deleting profile image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting profile image"
        )

@app.post("/auth/request-password-reset")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Yêu cầu đặt lại mật khẩu - Có kiểm tra tồn tại và giới hạn tần suất (Rate Limit)
    """
    try:
        logger.info(f"[PASSWORD_RESET] ===== START PASSWORD RESET REQUEST =====")
        logger.info(f"[PASSWORD_RESET] Email requested: {reset_request.email}")
        
        # 1. Kiểm tra user có tồn tại không (Yêu cầu của bạn: Báo lỗi nếu không có)
        result = await db.execute(select(User).where(User.email == reset_request.email))
        user = result.scalars().first()
        
        if not user:
            logger.warning(f"[PASSWORD_RESET] ❌ Email not found: {reset_request.email}")
            # Thay đổi logic: Báo lỗi trực tiếp
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản không tồn tại trong hệ thống"
            )
        
        # 2. Kiểm tra xem đã gửi link trước đó chưa (Dùng Redis)
        # Key format: password_reset_cooldown:{email}
        redis_key = f"password_reset_cooldown:{reset_request.email}"
        existing_request = await redis_client.get(redis_key)

        if existing_request:
            logger.warning(f"[PASSWORD_RESET] ⚠️ Request throttled for: {reset_request.email}")
            # Lấy thời gian còn lại (TTL)
            ttl = await redis_client.ttl(redis_key)
            minutes_left = ttl // 60
            seconds_left = ttl % 60
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Hoặc 429 Too Many Requests
                detail=f"Hệ thống đã gửi link đặt lại mật khẩu và vẫn còn hiệu lực trong {minutes_left} phút {seconds_left} giây nữa. Vui lòng kiểm tra hộp thư."
            )

        logger.info(f"[PASSWORD_RESET] ✓ User found: {user.user_id}")
        
        # 3. Tạo token đặt lại mật khẩu - hết hạn trong 5 phút
        TOKEN_EXPIRY_MINUTES = 5
        reset_token = create_access_token(
            data={"sub": user.email, "type": "password_reset"},
            expires_delta=timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        )
        
        # Tạo reset link
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        # 4. Gửi email
        user_full_name = f"{user.first_name} {user.last_name}".strip()
        email_service._reload_config() # Đảm bảo config mới nhất
        
        email_sent = await email_service.send_password_reset_email(
            user_email=user.email,
            user_name=user_full_name,
            reset_token=reset_token
        )
        
        if email_sent:
            # 5. Lưu vào Redis để chặn gửi lại trong 5 phút
            # Value là "1", expire là 5 phút (300 giây)
            await redis_client.setex(redis_key, TOKEN_EXPIRY_MINUTES * 60, "1")
            
            logger.info(f"[PASSWORD_RESET] ✅ SUCCESS - Email sent & Redis cooldown set")
            return {
                "success": True,
                "message": "Link đặt lại mật khẩu đã được gửi vào email của bạn"
            }
        else:
            logger.error(f"[PASSWORD_RESET] ❌ FAILED - Email service returned False")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể gửi email. Vui lòng thử lại sau."
            )

    except HTTPException:
        raise # Re-raise các lỗi HTTP đã định nghĩa (404, 400)
    except Exception as e:
        logger.error(f"[PASSWORD_RESET] ❌ EXCEPTION: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống: {str(e)}"
        )

@app.post("/auth/reset-password")
async def reset_password(
    request: Request,
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Xác nhận và thực hiện đặt lại mật khẩu
    """
    try:
        # Kiểm tra độ mạnh mật khẩu
        try:
            is_strong, error_message = security_utils.check_password_strength(reset_confirm.new_password)
            if not is_strong:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
        except AttributeError:
            pass
        
        # Xác thực token
        try:
            payload = jwt.decode(reset_confirm.token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            token_type = payload.get("type")
            
            # Kiểm tra token có phải là password reset token không
            if token_type != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token không hợp lệ"
                )
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token không chứa email"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token đã hết hạn hoặc không hợp lệ"
            )
        
        # Tìm user và cập nhật mật khẩu
        # SỬA: Chuyển sang cú pháp async với .where()
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng"
            )
        
        # Cập nhật mật khẩu
        user.password_hash = User.hash_password(reset_confirm.new_password)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Password reset successful for user {user.user_id}")
        
        return {
            "success": True,
            "message": "Mật khẩu đã được đặt lại thành công"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during password reset: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi đặt lại mật khẩu"
        )

# --- 7. Startup Event ---

@app.on_event("startup")
async def startup_event():
    """Khởi tạo database schema khi service khởi động"""
    try:
        await init_db()
        logger.info("Users service database initialized successfully")
        logger.info("✅ Database is ready for operation (seeding is handled by seed_manager)")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database initialization - will retry on next startup")

# --- 8. Main entry point ---

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Users Service directly...")
    uvicorn.run(app, host="0.0.0.0", port=8002)