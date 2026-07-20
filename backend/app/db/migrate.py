"""Migrasi ringan untuk dev/skeleton (SQLite).

`Base.metadata.create_all` cuma bikin tabel yang belum ada — dia TIDAK menambah
kolom baru ke tabel yang sudah terlanjur ada. Untuk skeleton (tanpa Alembic),
kita tambah kolom yang hilang secara idempotent lewat `ALTER TABLE ADD COLUMN`.

Production: ganti ini dengan Alembic migration betulan.
"""
import time

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError


def wait_for_db(engine: Engine, retries: int = 30, delay: float = 1.0) -> None:
    """Tunggu DB siap sebelum create_all — penting saat Postgres (Docker) baru
    warming up atau koneksi ke Supabase sempat belum stabil."""
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)

# tabel -> {kolom: definisi SQL untuk ADD COLUMN}
_ADDITIONS: dict[str, dict[str, str]] = {
    "users": {
        "supervisor_id": "INTEGER",
    },
    "wa_sessions": {
        "supervisor_id": "INTEGER",
    },
    "wa_broadcasts": {
        "approved_by": "INTEGER",
    },
    "wa_autoreplies": {
        "delay_seconds": "INTEGER DEFAULT 0",
    },
}


def run_light_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDITIONS.items():
            if table not in existing_tables:
                continue  # tabel baru — sudah dibuat lengkap oleh create_all
            present = {c["name"] for c in inspector.get_columns(table)}
            for col, coltype in columns.items():
                if col not in present:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {coltype}'))

        # Bootstrap: kalau belum ada admin sama sekali (mis. data lama dari
        # sebelum fitur role), promosikan user paling awal jadi admin.
        if "users" in existing_tables:
            has_admin = conn.execute(
                text("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")
            ).first()
            if not has_admin:
                first_id = conn.execute(
                    text("SELECT id FROM users ORDER BY id LIMIT 1")
                ).scalar()
                if first_id is not None:
                    conn.execute(
                        text("UPDATE users SET role = 'admin' WHERE id = :i"),
                        {"i": first_id},
                    )
