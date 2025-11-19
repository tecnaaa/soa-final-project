from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import Request
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# System metrics
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# Database metrics
DB_CONNECTION_POOL = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

DB_QUERY_LATENCY = Histogram(
    'db_query_duration_seconds',
    'Database query latency in seconds',
    ['operation']
)

# Service info
SERVICE_INFO = Info('service', 'Service information')

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response
    except Exception as e:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        raise e
    finally:
        ACTIVE_REQUESTS.dec()

def init_service_info(service_name: str, version: str):
    """Initialize service information metrics"""
    SERVICE_INFO.info({
        'name': service_name,
        'version': version,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
    })

def record_db_metrics():
    """Record database metrics"""
    from sqlalchemy import create_engine
    from db.db import engine
    
    # Get connection pool stats
    pool = engine.pool
    DB_CONNECTION_POOL.set(pool.size())

def start_metrics_collection():
    """Start collecting system metrics"""
    import psutil
    import threading
    
    def collect_system_metrics():
        while True:
            MEMORY_USAGE.set(psutil.Process().memory_info().rss)
            CPU_USAGE.set(psutil.Process().cpu_percent())
            time.sleep(15)  # Collect every 15 seconds
    
    thread = threading.Thread(target=collect_system_metrics, daemon=True)
    thread.start()