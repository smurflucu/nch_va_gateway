"""API key untuk aplikasi eksternal. Format: wa_<prefix8>_<secret>.
Yang disimpan cuma prefix (plain, buat lookup) + hash bcrypt dari secret."""
import secrets

from sqlalchemy.orm import Session as DbSession

from app.core.security import pwd_context
from app.models.wa import ApiKey
from app.repositories.wa_repository import ApiKeyRepository


class ApiKeyService:
    def __init__(self, db: DbSession):
        self.db = db
        self.repo = ApiKeyRepository(db)

    def create(self, user_id: int, name: str) -> tuple[ApiKey, str]:
        prefix = secrets.token_hex(4)          # 8 karakter
        secret = secrets.token_urlsafe(24)
        full_key = f"wa_{prefix}_{secret}"
        obj = ApiKey(
            user_id=user_id, name=name, prefix=prefix,
            key_hash=pwd_context.hash(secret),
        )
        return self.repo.create(obj), full_key

    def verify(self, full_key: str) -> ApiKey | None:
        """Kembalikan ApiKey kalau valid & aktif, else None."""
        try:
            _, prefix, secret = full_key.split("_", 2)
        except ValueError:
            return None
        for key in self.repo.list_by_prefix(prefix):
            if pwd_context.verify(secret, key.key_hash):
                return key
        return None
