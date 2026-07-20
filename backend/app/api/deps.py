from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, ROLE_ADMIN, ROLE_SUPERVISOR
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(repo)


def get_auth_service(repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(repo)


def get_current_user(
    request: Request,
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Baca access token dari Authorization: Bearer <token>."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError()
    user_id = decode_token(auth.removeprefix("Bearer ").strip(), expected_type="access")
    if not user_id:
        raise UnauthorizedError("Token invalid atau expired")
    user = repo.get(int(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError()
    return user


def require_role(*roles: str):
    """Factory RBAC guard. Contoh: `Depends(require_role(ROLE_ADMIN))`."""
    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"Butuh akses: {', '.join(roles)}")
        return user
    return _guard


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Guard endpoint yang hanya untuk admin (mis. input nomor WA, kelola user)."""
    if user.role != ROLE_ADMIN:
        raise ForbiddenError("Butuh akses admin")
    return user


def require_supervisor_or_admin(user: User = Depends(get_current_user)) -> User:
    """Guard untuk aksi level supervisor (kelola kontak/template, approve broadcast)."""
    if user.role not in (ROLE_ADMIN, ROLE_SUPERVISOR):
        raise ForbiddenError("Butuh akses supervisor atau admin")
    return user


def get_apikey_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Auth untuk endpoint gateway publik: header 'X-API-Key: wa_xxx_yyy'.
    Dipakai aplikasi eksternal untuk kirim pesan tanpa login JWT."""
    from datetime import datetime, timezone
    from app.services.apikey_service import ApiKeyService

    raw = request.headers.get("X-API-Key", "")
    if not raw:
        raise UnauthorizedError("Header X-API-Key wajib")
    key = ApiKeyService(db).verify(raw)
    if not key:
        raise UnauthorizedError("API key invalid atau nonaktif")
    key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    user = UserRepository(db).get(key.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError()
    return user
