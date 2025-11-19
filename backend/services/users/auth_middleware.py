import logging
from datetime import datetime
from fastapi import Request
from typing import Optional
import json

# Cấu hình logging
logging.basicConfig(
    filename='auth.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth_middleware')

class AuthLoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        # Log thời gian bắt đầu request
        start_time = datetime.now()
        
        # Thu thập thông tin request
        path = request.url.path
        method = request.method
        client_ip = request.client.host
        user_agent = request.headers.get('user-agent', 'Unknown')
        
        # Chuẩn bị log entry
        log_data = {
            'timestamp': start_time.isoformat(),
            'path': path,
            'method': method,
            'client_ip': client_ip,
            'user_agent': user_agent
        }
        
        try:
            # Thêm user ID nếu có
            auth_header = request.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                log_data['auth_present'] = True
            
            # Gọi next middleware/route handler
            response = await call_next(request)
            
            # Log kết quả
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            log_data.update({
                'status_code': response.status_code,
                'duration': duration
            })
            
            # Log theo mức độ dựa vào status code
            if response.status_code >= 500:
                logger.error(json.dumps(log_data))
            elif response.status_code >= 400:
                logger.warning(json.dumps(log_data))
            else:
                logger.info(json.dumps(log_data))
            
            return response
            
        except Exception as e:
            # Log lỗi
            log_data.update({
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            })
            logger.error(json.dumps(log_data))
            raise

def track_auth_activity(user_id: Optional[str], action: str, status: str, details: dict = None):
    """
    Ghi log hoạt động authentication cụ thể
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'action': action,
        'status': status
    }
    
    if details:
        log_data['details'] = details
        
    if status == 'failed':
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))

def setup_auth_logging(app):
    """
    Thiết lập middleware cho ứng dụng
    """
    app.middleware('http')(AuthLoggingMiddleware())