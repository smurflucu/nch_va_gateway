from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Semua setting dari .env — satu-satunya tempat baca environment."""
    APP_NAME: str = "MyWebApp"
    ENV: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = "http://localhost:5173"
    DATABASE_URL: str = "sqlite:///./app.db"

    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    SCHEDULER_TIMEZONE: str = "Asia/Jakarta"
    GOOGLE_CHAT_WEBHOOK: str = ""

    # WhatsApp gateway (service Node/Baileys)
    WA_GATEWAY_URL: str = "http://wa-gateway:3001"
    WA_INTERNAL_TOKEN: str = "change-me-internal-token"   # header ke Node
    WEBHOOK_SECRET: str = "change-me-webhook-secret"       # verifikasi webhook dari Node

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
