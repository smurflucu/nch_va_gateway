from app.core.exceptions import UnauthorizedError
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def authenticate(self, email: str, password: str) -> User:
        user = self.repo.get_by_email(email)
        # Pesan error sengaja generik — jangan bocorin email mana yang terdaftar
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Email atau password salah")
        if not user.is_active:
            raise UnauthorizedError("Akun tidak aktif")
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        return create_access_token(str(user.id)), create_refresh_token(str(user.id))

    def refresh(self, refresh_token: str) -> tuple[str, str, User]:
        user_id = decode_token(refresh_token, expected_type="refresh")
        if not user_id:
            raise UnauthorizedError("Refresh token invalid atau expired")
        user = self.repo.get(int(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User tidak valid")
        access, new_refresh = self.issue_tokens(user)
        return access, new_refresh, user
