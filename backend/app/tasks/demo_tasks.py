"""Task demo — jalan out-of-the-box tanpa dependency eksternal."""
from datetime import datetime, timedelta, timezone
from app.core.logging import get_logger

logger = get_logger("tasks.demo")


def heartbeat() -> str:
    now = datetime.now(timezone.utc).isoformat()
    logger.info("Heartbeat OK @ %s", now)
    return f"alive @ {now}"


def cleanup_old_job_runs() -> str:
    """Housekeeping: hapus history run lebih tua dari 30 hari."""
    from app.db.session import SessionLocal
    from app.models.job import JobRun

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    db = SessionLocal()
    try:
        deleted = db.query(JobRun).filter(JobRun.started_at < cutoff).delete()
        db.commit()
        return f"deleted {deleted} old runs"
    finally:
        db.close()
