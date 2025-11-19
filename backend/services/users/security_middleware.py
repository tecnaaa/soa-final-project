from fastapi import Request, HTTPException
from .security_monitoring import security_monitor

class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Lấy IP của client
        client_ip = request.client.host
        
        # Kiểm tra IP có trong blacklist không
        if security_monitor.is_ip_blacklisted(client_ip):
            raise HTTPException(
                status_code=403,
                detail="Your IP has been blocked due to suspicious activity"
            )
            
        # Theo dõi request API
        path = request.url.path
        method = request.method
        
        security_monitor.track_activity(
            'api_request',
            None,  # user_id sẽ được thêm sau nếu request được xác thực
            client_ip,
            {
                'path': path,
                'method': method
            }
        )
        
        # Xử lý request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Theo dõi lỗi
            security_monitor.track_activity(
                'api_error',
                None,
                client_ip,
                {
                    'path': path,
                    'method': method,
                    'error': str(e)
                }
            )
            raise