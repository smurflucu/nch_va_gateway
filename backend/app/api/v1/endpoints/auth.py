from fastapi import APIRouter, Depends, Request, Response
from app.api.deps import get_auth_service, get_user_service
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.middlewares.rate_limit import limiter
from app.schemas.token import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Refresh token di httpOnly cookie — tidak bisa dibaca JavaScript (aman dari XSS)."""
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.register(data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = service.authenticate(data.email, data.password)
    access, refresh = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh)
    # Access token dikirim di body -> frontend simpan di MEMORY, bukan localStorage
    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def refresh(request: Request, response: Response, service: AuthService = Depends(get_auth_service)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise UnauthorizedError("Refresh token tidak ada")
    access, new_refresh, _ = service.refresh(token)
    _set_refresh_cookie(response, new_refresh)  # rotation: refresh token baru setiap refresh
    return TokenResponse(access_token=access)


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
