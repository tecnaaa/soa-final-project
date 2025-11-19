"""API Gateway - Centralized entry point with resilience patterns"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
import httpx
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
import time
from collections import defaultdict
import os
from dotenv import load_dotenv
from typing import Optional, Dict
import uuid
from pathlib import Path

# Import new modules
from services.circuit_breaker import resilient_client
from services.event_bus import event_bus, Events
from services.structured_logging import configure_logging, ContextualLogger
from services.error_tracking import init_error_tracking, capture_error
import structlog

# Load environment variables
load_dotenv()

# Initialize error tracking
init_error_tracking("api_gateway")

# Configure logging
configure_logging("api_gateway", log_level="INFO")
logger = structlog.get_logger()

# Initialize FastAPI app with OpenAPI documentation
app = FastAPI(
    title="Fitness Dashboard API Gateway",
    description="Centralized API Gateway with Event-Driven Architecture",
    version="2.0.0"
)

# Rate limiting configuration
RATE_LIMIT_DURATION = 60  # seconds
RATE_LIMIT_REQUESTS = 100  # requests per duration
rate_limit_store: Dict[str, list] = defaultdict(list)

# Security configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

# Middleware to add request ID and logging
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Request processed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time
    )
    
    response.headers["X-Request-ID"] = request_id
    return response

# Middleware to add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value
    return response

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Clear old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < RATE_LIMIT_DURATION
    ]
    
    # Check rate limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests",
                "wait_time": RATE_LIMIT_DURATION - (now - rate_limit_store[client_ip][0])
            }
        )
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    
    # Process request
    response = await call_next(request)
    return response

# CORS configuration with stricter settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    max_age=600
)

users_service_url = os.getenv("USERS_SERVICE_URL", "http://localhost:8002") # Khai báo biến này

SERVICE_URLS = {
    "users": users_service_url, # Dùng biến vừa khai báo
    "workout": os.getenv("WORKOUT_SERVICE_URL", "http://localhost:8003"),
    "nutrition": os.getenv("NUTRITION_SERVICE_URL", "http://localhost:8004"),
    "calories": os.getenv("CALORIES_SERVICE_URL", "http://localhost:8005"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8007"),
    "files": f"{users_service_url}/files", # THÊM DÒNG NÀY: Route files trỏ về Users Service
}

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Event bus initialization
async def init_event_bus():
    """Initialize event bus on startup"""
    try:
        await event_bus.connect()
        logger.info("Event Bus initialized")
    except Exception as e:
        logger.error("Failed to initialize Event Bus", error=str(e))

async def shutdown_event_bus():
    """Shutdown event bus on shutdown"""
    try:
        await event_bus.disconnect()
        logger.info("Event Bus disconnected")
    except Exception as e:
        logger.error("Failed to disconnect Event Bus", error=str(e))

app.add_event_handler("startup", init_event_bus)
app.add_event_handler("shutdown", shutdown_event_bus)

async def verify_token_optional(request: Request):
    """Xác thực JWT token - tùy chọn (không bắt buộc)"""
    try:
        if "authorization" not in request.headers:
            return None  # Token không bắt buộc
        
        token = request.headers["authorization"].split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Kiểm tra thêm các claims
            if "exp" not in payload:
                return None
            
            if payload["exp"] < time.time():
                return None
                
            if "sub" not in payload:
                return None
                
            return payload
            
        except (ExpiredSignatureError, JWTError):
            return None
    except Exception:
        return None

async def verify_token(request: Request):
    """Xác thực JWT token với kiểm tra bổ sung"""
    try:
        if "authorization" not in request.headers:
            raise HTTPException(
                status_code=401,
                detail="No authorization token"
            )
        
        token = request.headers["authorization"].split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Kiểm tra thêm các claims
            if "exp" not in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Token missing expiration"
                )
            
            if payload["exp"] < time.time():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )
                
            if "sub" not in payload:
                raise HTTPException(
                    status_code=401,
                    detail="Token missing subject"
                )
                
            return payload
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

def requires_auth(roles: list = None):
    """Middleware để kiểm tra quyền truy cập"""
    async def wrapper(request: Request):
        payload = await verify_token(request)
        if roles and payload.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return payload
    return wrapper

# Public endpoints (no auth required) - MUST BE BEFORE generic proxy route
@app.post("/auth/login", tags=["Authentication"])
async def login(request: Request):
    """
    Login endpoint - Authenticate user and return JWT tokens
    
    **Event Published**: USER_LOGIN_ATTEMPTED
    """
    client_ip = request.client.host
    request_id = request.state.request_id
    
    # Specialized rate limiting for login attempts
    login_attempts = len([
        t for t in rate_limit_store.get(f"login_{client_ip}", [])
        if time.time() - t < 300  # 5 minutes window
    ])
    
    if login_attempts >= 5:
        await event_bus.publish(
            Events.USER_CREATED,
            {"client_ip": client_ip, "reason": "too_many_login_attempts"}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later."
        )
    
    rate_limit_store[f"login_{client_ip}"] = rate_limit_store.get(f"login_{client_ip}", []) + [time.time()]
    
    try:
        body = await request.json()
        logger.info(f"Login request body: {body}")
        # Sử dụng service="users" thay vì gọi trực tiếp để tận dụng circuit breaker dictionary
        response = await resilient_client.post(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/login",
            json=body,
        )
        
        logger.info("User login successful", request_id=request_id)
        return response.json()

    except httpx.HTTPStatusError as e:
        # Bắt lỗi 4xx từ service (VD: sai pass)
        logger.warning(
            f"Login failed (HTTPStatusError): {e.response.status_code}",
            request_id=request_id
        )
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )
        
    except Exception as e:
        logger.error("Login failed (Service Error)", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Login service error: {str(e)}"
        )

@app.post("/auth/refresh", tags=["Authentication"])
async def refresh_token(request: Request):
    """
    Refresh token endpoint - Get new access token using refresh token
    """
    request_id = request.state.request_id
    
    try:
        response = await resilient_client.post(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/auth/refresh",
            json=await request.json(),
            headers=SECURITY_HEADERS
        )
        
        logger.info("Token refreshed successfully", request_id=request_id)
        return response.json()
    except Exception as e:
        logger.error("Token refresh failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh error: {str(e)}"
        )

@app.post("/auth/register", tags=["Authentication"])
async def register(request: Request):
    """
    Register new user endpoint
    
    **Event Published**: USER_CREATED
    """
    request_id = request.state.request_id
    
    try:
        body = await request.json()
        response = await resilient_client.post(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/register",
            json=body,
            headers=SECURITY_HEADERS
        )
        
        result = response.json()
        
        # Publish user created event
        await event_bus.publish(
            Events.USER_CREATED,
            {
                "user_id": result.get("id"),
                "email": body.get("email"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info("User registered", request_id=request_id, 
                   email=body.get("email"))
        return result
    except Exception as e:
        logger.error("Registration failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Registration service error: {str(e)}"
        )

@app.post("/auth/request-password-reset", tags=["Authentication"])
async def request_password_reset(request: Request):
    """
    Request password reset endpoint
    """
    request_id = request.state.request_id
    
    try:
        body = await request.json()
        logger.info(f"Password reset request for email: {body.get('email')}", request_id=request_id)
        
        response = await resilient_client.post(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/auth/request-password-reset",
            json=body
        )
        
        return JSONResponse(
            status_code=response.status_code, 
            content=response.json()
        )

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Reset request failed (Client Error): {e.response.status_code}",
            request_id=request_id,
            detail=e.response.text
        )
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )

    except Exception as e:
        logger.error("Password reset request failed (Service Error)", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Password reset service error: {str(e)}"
        )

@app.post("/auth/reset-password", tags=["Authentication"])
async def reset_password(request: Request):
    """
    Reset password endpoint - Confirm password reset with token
    """
    request_id = request.state.request_id
    
    try:
        body = await request.json()
        logger.info("Password reset confirmation received", request_id=request_id)
        
        response = await resilient_client.post(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/auth/reset-password",
            json=body
        )
        
        logger.info("Password reset successful", request_id=request_id)
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Password reset failed (HTTPStatusError): {e.response.status_code}",
            request_id=request_id,
            response=e.response.json()
        )
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )

    except Exception as e:
        logger.error("Password reset failed (Service Error)", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Password reset service error: {str(e)}"
        )

@app.get("/users/me", tags=["Users"], response_class=JSONResponse)
async def get_current_user(request: Request):
    """
    Get current user info endpoint
    Requires valid access token
    """
    request_id = request.state.request_id
    
    try:
        if "authorization" not in request.headers:
            logger.warning("No authorization header in request", request_id=request_id)
            raise HTTPException(
                status_code=401,
                detail="No authorization token"
            )
        
        auth_header = request.headers["authorization"]
        logger.info(f"Auth header present: {auth_header[:30]}...", request_id=request_id)
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
        }
        
        response = await resilient_client.get(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/users/me",
            headers=headers
        )
        
        logger.info("Fetched current user", request_id=request_id, status=response.status_code)
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch current user", request_id=request_id, error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=503,
            detail=f"User service error: {str(e)}"
        )

@app.put("/users/me", tags=["Users"], response_class=JSONResponse)
async def update_current_user(request: Request):
    """
    Update current user info endpoint
    Requires valid access token
    """
    request_id = request.state.request_id
    
    try:
        if "authorization" not in request.headers:
            logger.warning("No authorization header in request", request_id=request_id)
            raise HTTPException(
                status_code=401,
                detail="No authorization token"
            )
        
        auth_header = request.headers["authorization"]
        body = await request.json()
        
        logger.info(
            "Attempting to update user",
            request_id=request_id,
            body_keys=list(body.keys()) if body else None
        )
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
        }
        
        response = await resilient_client.put(
            service_name="users",
            url=f"{SERVICE_URLS['users']}/users/me",
            json=body,
            headers=headers
        )
        
        logger.info(
            "User updated successfully",
            request_id=request_id,
            status_code=response.status_code
        )
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update current user",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=503,
            detail=f"User service error: {str(e)}"
        )

# Health check endpoint - MUST BE BEFORE generic proxy route
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint - Verify all services are running
    Returns status of all microservices
    """
    status = {}
    
    for service, url in SERVICE_URLS.items():
        try:
            # Check health endpoint of each service
            # Note: 'files' is a pseudo-service pointing to 'users', so we skip or map it
            check_url = url
            if service == "files": 
                continue # Skip checking 'files' as it's just a path in 'users'
                
            response = await resilient_client.get(
                service_name=service if service != "files" else "users",
                url=f"{check_url}/health",
                timeout=2.0
            )
            status[service] = "up" if response.status_code == 200 else "down"
        except Exception:
            status[service] = "down"
    
    logger.info("Health check performed", services=status)
    return {"status": status, "timestamp": datetime.utcnow().isoformat()}

# Circuit Breaker Status endpoint - MUST BE BEFORE generic proxy route
@app.get("/monitoring/circuits", tags=["Monitoring"])
async def get_circuit_status():
    """
    Get circuit breaker status for all services
    Useful for monitoring service health
    """
    return {
        "circuits": resilient_client.get_all_circuit_status(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/monitoring/circuits/reset/{service_name}", tags=["Monitoring"])
async def reset_circuit_breaker(service_name: str):
    """
    Reset circuit breaker cho một service cụ thể
    """
    if service_name not in resilient_client.circuit_breakers:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_name}' circuit not found"
        )
    
    circuit = resilient_client.circuit_breakers[service_name]
    circuit.reset()
    
    logger.info(f"Circuit breaker for service '{service_name}' has been manually reset", 
                service=service_name)
    
    return {
        "message": f"Circuit breaker for '{service_name}' has been reset",
        "status": circuit.get_status(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Generic proxy route MUST BE LAST
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(
    service: str,
    path: str,
    request: Request
):
    """Proxy request đến service với Circuit Breaker & Event Bus"""
    if service not in SERVICE_URLS:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service}' not found"
        )
    
    # Xác thực token nếu được yêu cầu (tùy chọn)
    token = None
    if "authorization" in request.headers:
        try:
            auth_header = request.headers["authorization"]
            token_str = auth_header.split(" ")[1]
            token = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            # Token không hợp lệ - sẽ được xử lý bởi service
            pass
    
    # Một số endpoints yêu cầu token (ngoại trừ files)
    protected_paths = [
        "/users/me",
        "/workout/",
        "/nutrition/",
        "/calories/",
        "/payment/"
    ]
    
    # Thêm điều kiện if service != "files":
    if service != "files":
        is_protected = any(path.startswith(p) for p in protected_paths)
        
        if is_protected and not token:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
    
    target_url = f"{SERVICE_URLS[service]}/{path}"
    request_id = request.state.request_id
    
    try:
        # Get request body if any
        body = await request.body()
        
        # Forward request with circuit breaker
        # Nếu service là 'files', dùng circuit breaker của 'users' (để tránh tạo circuit riêng cho file tĩnh)
        target_service_name = "users" if service == "files" else service
        
        response = await resilient_client.request(
            service_name=target_service_name,
            method=request.method,
            url=target_url,
            content=body,
            headers={
                **SECURITY_HEADERS,
                "Authorization": request.headers.get("authorization"),
                "Content-Type": request.headers.get("content-type", "application/json"),
                "X-Forwarded-For": request.client.host,
                "X-Request-ID": request_id
            }
        )
        
        logger.info(
            "Request proxied successfully",
            service=service,
            path=path,
            status_code=response.status_code
        )
        
        # --- CẬP NHẬT QUAN TRỌNG: Xử lý response dựa trên Content-Type ---
        content_type = response.headers.get("content-type", "")
        
        if "application/json" in content_type:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json(),
                headers=SECURITY_HEADERS
            )
        else:
            # Trả về raw content cho file ảnh/binary
            # Lọc bỏ các header hop-by-hop có thể gây lỗi
            excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
            headers = {k: v for k, v in response.headers.items() if k.lower() not in excluded_headers}
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=content_type,
                headers=headers
            )
            
    except Exception as e:
        logger.error(
            "Proxy request failed",
            service=service,
            path=path,
            error=str(e)
        )
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )

# OpenAPI Custom Schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Fitness Dashboard API",
        version="2.0.0",
        description="Event-Driven Microservices Architecture with API Gateway",
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )