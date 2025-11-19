import logging
import logging.config
import json
import sys
import os
from pythonjsonlogger import jsonlogger
from datetime import datetime
from typing import Any, Dict

def setup_logging(service_name: str) -> None:
    """
    Set up logging for the service using configuration from logging.conf
    """
    config_path = os.path.join(os.path.dirname(__file__), '../config/logging.conf')
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path)
    else:
        # Fallback configuration if file doesn't exist
        configure_default_logging(service_name)

def configure_default_logging(service_name: str) -> None:
    """
    Configure default JSON logging if config file is not available
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomJsonFormatter())
    logger.addHandler(console_handler)

    # File handler
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        f'logs/{service_name}.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(CustomJsonFormatter())
    logger.addHandler(file_handler)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional fields
    """
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add ISO format timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

        # Add call info
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        log_record['path'] = record.pathname

        # Add process and thread info
        log_record['process_id'] = record.process
        log_record['process_name'] = record.processName
        log_record['thread_id'] = record.thread
        log_record['thread_name'] = record.threadName

def get_logger(service_name: str) -> logging.Logger:
    """
    Get a configured logger for the service
    """
    logger = logging.getLogger(service_name)
    
    # Add handlers if none exist
    if not logger.handlers:
        setup_logging(service_name)
    
    return logger

def log_request(logger: logging.Logger, request: Any, response: Any = None, error: Exception = None) -> None:
    """
    Log request and response details
    """
    log_data = {
        'request_method': getattr(request, 'method', None),
        'request_url': str(getattr(request, 'url', '')),
        'client_ip': getattr(request, 'client', None),
        'user_agent': getattr(request.headers, 'user-agent', None),
    }

    if response:
        log_data.update({
            'response_status': getattr(response, 'status_code', None),
            'response_time': getattr(response, 'elapsed', None),
        })

    if error:
        log_data.update({
            'error': str(error),
            'error_type': error.__class__.__name__,
        })
        logger.error('Request failed', extra=log_data)
    else:
        logger.info('Request processed', extra=log_data)

def log_db_operation(logger: logging.Logger, operation: str, query: str, params: Dict = None, error: Exception = None) -> None:
    """
    Log database operations
    """
    log_data = {
        'operation': operation,
        'query': query,
        'parameters': params,
    }

    if error:
        log_data.update({
            'error': str(error),
            'error_type': error.__class__.__name__,
        })
        logger.error('Database operation failed', extra=log_data)
    else:
        logger.info('Database operation successful', extra=log_data)