from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, Type
import traceback
import logging
import json
from datetime import datetime
from prometheus_client import Counter
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import os
from dotenv import load_dotenv

load_dotenv()

# Error metrics
ERROR_COUNTER = Counter(
    'application_errors_total',
    'Total error count by type and service',
    ['error_type', 'service']
)

class BaseServiceError(Exception):
    """Base exception class for service errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }

class ValidationError(BaseServiceError):
    """Raised when request validation fails"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AuthenticationError(BaseServiceError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )

class AuthorizationError(BaseServiceError):
    """Raised when user lacks required permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )

class ResourceNotFoundError(BaseServiceError):
    """Raised when requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with id {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": str(resource_id)}
        )

class DatabaseError(BaseServiceError):
    """Raised when database operations fail"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {
            "error_type": type(original_error).__name__ if original_error else None,
            "error_details": str(original_error) if original_error else None
        }
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details
        )

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for all services"""
    logger = logging.getLogger('error_handler')

    if isinstance(exc, BaseServiceError):
        error_response = exc.to_dict()
        status_code = exc.status_code
    else:
        # Handle unexpected errors
        error_response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        status_code = 500

        # Log the full error details
        logger.error(
            "Unhandled exception",
            extra={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                "request_path": request.url.path,
                "request_method": request.method,
            }
        )

    # Increment error counter
    ERROR_COUNTER.labels(
        error_type=error_response["error"]["code"],
        service=request.app.title
    ).inc()

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

def setup_error_handling(app: Any) -> None:
    """Configure error handling for a FastAPI application"""
    # Register error handlers
    app.add_exception_handler(BaseServiceError, error_handler)
    app.add_exception_handler(Exception, error_handler)

    # Add error tracking middleware
    @app.middleware("http")
    async def error_tracking_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return await error_handler(request, exc)

def init_error_tracking(service_name: str):
    """Initialize error tracking for the given service"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    # Only initialize Sentry if DSN is configured
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv('ENVIRONMENT', 'development'),
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            release=service_name,  # Use release instead of service_name
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            send_default_pii=False,
            before_send=before_send,
        )
        logger = logging.getLogger('error_tracking')
        logger.info(f"Sentry error tracking initialized for {service_name}")
    else:
        # Skip Sentry if DSN not configured
        logger = logging.getLogger('error_tracking')
        logger.debug(f"Sentry not configured (SENTRY_DSN not set) for {service_name}")

def before_send(event, hint):
    """Process and sanitize error events before sending"""
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        # Sanitize sensitive information
        if 'user' in event:
            del event['user']['ip_address']
        if 'request' in event:
            # Remove sensitive headers
            sensitive_headers = ['authorization', 'cookie']
            event['request']['headers'] = {
                k: v for k, v in event['request']['headers'].items()
                if k.lower() not in sensitive_headers
            }
    return event

def capture_error(error, context=None):
    """Capture an error with additional context"""
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)