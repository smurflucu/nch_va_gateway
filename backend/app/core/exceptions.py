from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception aplikasi — semua custom error turunan dari sini."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, 401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, 409)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
