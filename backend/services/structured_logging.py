"""
Structured Logging - Centralized logging system
"""
import structlog
import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os

# Configure structlog
def configure_logging(service_name: str, log_level: str = "INFO"):
    """
    Cấu hình structured logging cho service
    
    Args:
        service_name: Tên service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Tạo folder logs nếu chưa tồn tại
    os.makedirs("logs", exist_ok=True)
    
    # Tạo JSON formatter cho file logging
    json_handler = logging.FileHandler(
        f"logs/{service_name}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    json_handler.setFormatter(
        jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
    )
    
    # Tạo console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[console_handler, json_handler]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class ContextualLogger:
    """Logger with request context"""
    
    def __init__(self, service_name: str, request_id: str = None):
        self.logger = structlog.get_logger()
        self.service_name = service_name
        self.request_id = request_id
    
    def log(self, level: str, message: str, **kwargs):
        """Log với context"""
        log_data = {
            "service": self.service_name,
            "request_id": self.request_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message, **log_data)
    
    def info(self, message: str, **kwargs):
        self.log("info", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log("error", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log("warning", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self.log("debug", message, **kwargs)


def get_logger(service_name: str) -> structlog.PrintLogger:
    """Lấy logger cho service"""
    return structlog.get_logger()
