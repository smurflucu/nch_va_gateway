"""Broadcast/blast ke banyak nomor.
- Dijalankan di thread scheduler (non-blocking untuk HTTP).
- Ada jeda antar pesan (delay_seconds) — penting biar nomor tidak cepat kena banned.
- Personalisasi sederhana: {{name}} di body diganti nama target.
"""
import json
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DbSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.user import User, ROLE_USER
from app.models.wa import Broadcast, Message
from app.repositories.wa_repository import BroadcastRepository, SessionRepository
from app.schemas.wa import BroadcastCreate
from app.services import scope
from app.services import wa_gateway_client as gateway
from app.utils.validators import normalize_phone

logger = get_logger("wa.broadcast")


def _render(body: str, name: str) -> str:
    return body.replace("{{name}}", name or "").replace("{{nama}}", name or "")


class BroadcastService:
    def __init__(self, db: DbSession):
        self.db = db
        self.repo = BroadcastRepository(db)
        self.sessions = SessionRepository(db)

    def list_for(self, actor: User) -> list[Broadcast]:
        return self.repo.list_scoped(scope.visible_user_ids(self.db, actor))

    def list_pending(self, actor: User) -> list[Broadcast]:
        """Antrian approval — untuk supervisor (timnya) / admin (semua)."""
        return self.repo.list_pending_for_team(scope.visible_user_ids(self.db, actor))

    def get_or_404(self, actor: User, broadcast_id: int) -> Broadcast:
        bc = self.repo.get_scoped(broadcast_id, scope.visible_user_ids(self.db, actor))
        if not bc:
            raise NotFoundError("Broadcast tidak ditemukan")
        return bc

    def create(self, actor: User, data: BroadcastCreate) -> Broadcast:
        # Nomor harus milik tim si actor
        wa = self.sessions.get_for_team(data.session_id, scope.team_owner_id(actor))
        if not wa:
            raise NotFoundError("Session tidak ditemukan")
        targets = [{"phone": normalize_phone(t.phone), "name": t.name} for t in data.targets]
        scheduled = data.scheduled_at is not None
        is_regular = actor.role == ROLE_USER

        # Regular user: broadcast masuk antrian approval, TIDAK langsung jalan.
        if is_regular:
            status = "pending_approval"
        else:
            status = "scheduled" if scheduled else "running"

        bc = Broadcast(
            user_id=actor.id, session_id=wa.id, name=data.name, body=data.body,
            targets=json.dumps(targets, ensure_ascii=False),
            delay_seconds=data.delay_seconds,
            status=status,
            scheduled_at=data.scheduled_at, total=len(targets),
        )
        bc = self.repo.create(bc)
        if status == "running":
            enqueue(bc.id)  # supervisor/admin tanpa jadwal → jalan sekarang
        return bc

    def approve(self, actor: User, broadcast_id: int) -> Broadcast:
        """Supervisor/admin menyetujui broadcast regular user."""
        bc = self.get_or_404(actor, broadcast_id)
        if bc.status != "pending_approval":
            raise ForbiddenError("Broadcast ini tidak menunggu approval")
        bc.approved_by = actor.id
        if bc.scheduled_at is not None:
            bc.status = "scheduled"
            bc = self.repo.update(bc)
        else:
            bc.status = "running"
            bc = self.repo.update(bc)
            enqueue(bc.id)
        return bc

    def reject(self, actor: User, broadcast_id: int) -> Broadcast:
        bc = self.get_or_404(actor, broadcast_id)
        if bc.status != "pending_approval":
            raise ForbiddenError("Broadcast ini tidak menunggu approval")
        bc.approved_by = actor.id
        bc.status = "rejected"
        return self.repo.update(bc)


def enqueue(broadcast_id: int) -> None:
    """Titip ke scheduler supaya jalan di thread-nya (import lazy hindari circular)."""
    from app.services.scheduler_service import scheduler
    scheduler.add_job(
        run_broadcast, args=[broadcast_id],
        id=f"broadcast-{broadcast_id}-{datetime.now(timezone.utc).timestamp()}",
        max_instances=1,
    )


def run_broadcast(broadcast_id: int) -> str:
    """Eksekusi aktual — punya DB session sendiri (dipanggil dari thread scheduler)."""
    db = SessionLocal()
    try:
        bc = db.get(Broadcast, broadcast_id)
        if not bc:
            return "broadcast tidak ada"
        from app.models.wa import WaSession
        wa = db.get(WaSession, bc.session_id)
        if not wa:
            bc.status = "failed"
            db.commit()
            return "session tidak ada"

        bc.status = "running"
        db.commit()
        targets = json.loads(bc.targets or "[]")
        sent = failed = 0
        for i, t in enumerate(targets):
            phone = t.get("phone", "")
            body = _render(bc.body, t.get("name", ""))
            msg = Message(user_id=bc.user_id, session_id=wa.id, direction="out",
                          chat_number=phone, body=body, status="sent")
            try:
                res = gateway.send_message(wa.session_key, phone, body)
                msg.wa_message_id = res.get("id", "")
                sent += 1
            except Exception as e:  # noqa: BLE001
                msg.status = "failed"
                msg.error = str(e)[:255]
                failed += 1
            db.add(msg)
            bc.sent, bc.failed = sent, failed
            db.commit()
            if i < len(targets) - 1 and bc.delay_seconds:
                time.sleep(bc.delay_seconds)

        bc.status = "done"
        db.commit()
        logger.info("Broadcast '%s' selesai: %d terkirim, %d gagal", bc.name, sent, failed)
        return f"terkirim {sent}, gagal {failed}"
    finally:
        db.close()
