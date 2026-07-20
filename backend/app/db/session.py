from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    # pool_pre_ping: cek koneksi sebelum dipakai — WAJIB untuk DB cloud (Supabase)
    # yang memutus koneksi idle; menghindari error "server closed the connection".
    pool_pre_ping=not _is_sqlite,
    # daur ulang koneksi tiap 30 mnt (aman untuk pooler Supabase).
    pool_recycle=1800 if not _is_sqlite else -1,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: satu session per request, auto-close."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
