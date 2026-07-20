from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import setup_logging
from app.db.session import Base, engine
from app.db.migrate import run_light_migrations, wait_for_db
from app.models import user as _user_model, job as _job_model, wa as _wa_model  # noqa: F401 — daftarkan tabel
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.rate_limit import limiter
from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.services.scheduler_service import start_scheduler, stop_scheduler

setup_logging(settings.DEBUG)

# Tunggu DB siap (Postgres Docker warming up / koneksi Supabase), lalu
# auto-create table + migrasi ringan. Production: pakai Alembic migration.
wait_for_db(engine)
Base.metadata.create_all(bind=engine)
run_light_migrations(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    docs_url="/docs" if settings.DEBUG else None,  # matikan Swagger di production
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppException, app_exception_handler)

app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # whitelist, bukan *
    allow_credentials=True,                    # wajib untuk httpOnly cookie
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router)
