import time
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log setiap request: method, path, status, durasi. Tanpa body (bisa berisi data sensitif)."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
        return response
