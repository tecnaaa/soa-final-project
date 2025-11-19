from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
import redis
from typing import Optional

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class RefreshTokenHandler:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        
    def create_tokens(self, user_data: dict) -> tuple[str, str]:
        """Tạo cặp access token và refresh token mới"""
        # Tạo access token
        access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_data = {
            **user_data,
            "exp": access_token_expires.timestamp()
        }
        access_token = jwt.encode(
            access_token_data,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        
        # Tạo refresh token
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_data = {
            "sub": user_data["sub"],
            "exp": refresh_token_expires.timestamp(),
            "token_type": "refresh"
        }
        refresh_token = jwt.encode(
            refresh_token_data,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        
        # Lưu refresh token vào Redis với thời gian hết hạn
        self.redis_client.setex(
            f"refresh_token:{user_data['sub']}",
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            refresh_token
        )
        
        return access_token, refresh_token
        
    def verify_refresh_token(self, refresh_token: str) -> Optional[dict]:
        """Xác thực refresh token và trả về thông tin user"""
        try:
            # Giải mã token
            payload = jwt.decode(
                refresh_token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            
            # Kiểm tra loại token
            if payload.get("token_type") != "refresh":
                return None
                
            # Kiểm tra token có trong Redis không
            stored_token = self.redis_client.get(f"refresh_token:{payload['sub']}")
            if not stored_token or stored_token != refresh_token:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            # Xóa token hết hạn khỏi Redis
            if "sub" in payload:
                self.redis_client.delete(f"refresh_token:{payload['sub']}")
            return None
        except jwt.JWTError:
            return None
            
    def revoke_refresh_token(self, user_id: str):
        """Thu hồi refresh token của user"""
        self.redis_client.delete(f"refresh_token:{user_id}")
        
    def revoke_all_tokens(self, user_id: str):
        """Thu hồi tất cả refresh token của user (đăng xuất khỏi tất cả thiết bị)"""
        pattern = f"refresh_token:{user_id}:*"
        tokens = self.redis_client.keys(pattern)
        if tokens:
            self.redis_client.delete(*tokens)
            
# Singleton instance
refresh_token_handler = RefreshTokenHandler()

async def refresh_token_middleware(request: Request, call_next):
    """Middleware xử lý refresh token"""
    try:
        response = await call_next(request)
        
        # Nếu response là lỗi token hết hạn
        if response.status_code == 401 and "Token has expired" in str(response.body):
            # Kiểm tra refresh token trong header
            refresh_token = request.headers.get("refresh-token")
            if not refresh_token:
                return response
                
            # Xác thực refresh token
            payload = refresh_token_handler.verify_refresh_token(refresh_token)
            if not payload:
                return response
                
            # Tạo token mới
            user_data = {
                "sub": payload["sub"],
                "role": payload.get("role", "user")
            }
            new_access_token, new_refresh_token = refresh_token_handler.create_tokens(user_data)
            
            # Thêm token mới vào response headers
            response.headers["new-access-token"] = new_access_token
            response.headers["new-refresh-token"] = new_refresh_token
            
        return response
    except Exception as e:
        return response