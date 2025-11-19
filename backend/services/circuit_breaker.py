"""
Circuit Breaker Pattern - Xử lý failures trong service-to-service communication
"""
import httpx
import time
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Trạng thái của circuit breaker"""
    CLOSED = "closed"        # Bình thường
    OPEN = "open"           # Service down
    HALF_OPEN = "half_open"  # Đang test


class CircuitBreaker:
    """
    Circuit Breaker implementation cho HTTP calls
    Giúp tránh gọi service bị lỗi liên tục
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 10,
        success_threshold: int = 2,
        timeout_duration: int = 120
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_duration = timeout_duration
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
    
    def can_execute(self) -> bool:
        """Kiểm tra có thể execute request không"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit {self.name} is HALF_OPEN")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def _should_attempt_reset(self) -> bool:
        """Kiểm tra có nên reset circuit không"""
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_duration
    
    def record_success(self):
        """Ghi nhận successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit {self.name} is CLOSED")
    
    def record_failure(self):
        """Ghi nhận failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit {self.name} is OPEN",
                failure_count=self.failure_count
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Trả về trạng thái hiện tại của circuit"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() 
                if self.last_failure_time else None
        }
    
    def reset(self):
        """Reset circuit breaker trở về trạng thái ban đầu"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit {self.name} has been reset to CLOSED")


class ResilientHttpClient:
    """HTTP client với Circuit Breaker & Retry logic"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Lấy hoặc tạo circuit breaker cho service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(service_name)
        return self.circuit_breakers[service_name]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def request(
        self,
        service_name: str,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Gọi HTTP request với circuit breaker & retry
        
        Args:
            service_name: Tên service cho circuit breaker tracking
            method: HTTP method (GET, POST, etc.)
            url: URL
            **kwargs: Additional httpx.AsyncClient.request arguments
        """
        circuit = self._get_circuit_breaker(service_name)
        
        if not circuit.can_execute():
            raise Exception(
                f"Service {service_name} is unavailable (circuit OPEN)"
            )
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # CHỈ ném lỗi và ghi nhận failure cho lỗi 5xx (Server Error)
            if response.status_code >= 500:
                response.raise_for_status()

            # Coi các phản hồi 2xx, 3xx, và 4xx (lỗi client) là thành công
            # vì service đã xử lý và phản hồi đúng
            circuit.record_success()
            return response

        except httpx.HTTPStatusError as e: # Chỉ bắt lỗi 5xx
            circuit.record_failure()
            logger.error(
                f"Request to {service_name} failed (Server Error)",
                service=service_name,
                url=url,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise e
        except httpx.RequestError as e: # Bắt lỗi mạng (Timeout, Connection Error...)
            circuit.record_failure()
            logger.error(
                f"Request to {service_name} failed (Request Error)",
                service=service_name,
                url=url,
                error=str(e)
            )
            raise e
        except Exception as e: # Các lỗi khác
            circuit.record_failure()
            logger.error(
                f"Request to {service_name} failed (Unexpected Error)",
                service=service_name,
                url=url,
                error=str(e)
            )
            raise e
    
    async def get(self, service_name: str, url: str, **kwargs) -> httpx.Response:
        """GET request"""
        return await self.request(service_name, "GET", url, **kwargs)
    
    async def post(self, service_name: str, url: str, **kwargs) -> httpx.Response:
        """POST request"""
        return await self.request(service_name, "POST", url, **kwargs)
    
    async def put(self, service_name: str, url: str, **kwargs) -> httpx.Response:
        """PUT request"""
        return await self.request(service_name, "PUT", url, **kwargs)
    
    async def delete(self, service_name: str, url: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        return await self.request(service_name, "DELETE", url, **kwargs)
    
    def get_all_circuit_status(self) -> Dict[str, Any]:
        """Lấy trạng thái tất cả circuits"""
        return {
            name: circuit.get_status()
            for name, circuit in self.circuit_breakers.items()
        }
    
    async def close(self):
        """Đóng client"""
        await self.client.aclose()


# Singleton instance
resilient_client = ResilientHttpClient()
