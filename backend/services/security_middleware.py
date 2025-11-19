from fastapi import Request, HTTPException

class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Lấy IP của client
        client_ip = request.client.host if request.client else "unknown"
        
        # Xử lý request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log lỗi
            raise