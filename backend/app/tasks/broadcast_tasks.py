"""Task terjadwal: cek broadcast yang waktunya sudah tiba, lalu jalankan.
Di-seed sebagai job 'dispatch-broadcasts' yang jalan tiap menit."""
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.wa_repository import BroadcastRepository
from app.services.broadcast_service import enqueue

logger = get_logger("tasks.broadcast")


def dispatch_due_broadcasts() -> str:
    db = SessionLocal()
    try:
        repo = BroadcastRepository(db)
        due = repo.list_due(datetime.now(timezone.utc))
        for bc in due:
            bc.status = "running"  # tandai supaya tidak dobel di menit berikutnya
            db.commit()
            enqueue(bc.id)
        return f"dispatched {len(due)} broadcast"
    finally:
        db.close()
