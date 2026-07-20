"""Business logic WhatsApp: kelola sesi, kirim pesan (+log), proses webhook & auto-reply.

Scoping RBAC:
- Nomor (WaSession) dimiliki satu TIM (supervisor_id). Hanya admin yang input/hapus.
- Supervisor + regular user di timnya boleh memakai (kirim) nomor tim.
- Inbox: regular hanya lihat percakapan yang DIA mulai (conversation ownership);
  supervisor lihat seluruh tim; admin lihat semua.
"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session as DbSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.user import User
from app.models.wa import WaSession, Message, AutoReply, Broadcast
from app.repositories.wa_repository import (
    SessionRepository, MessageRepository, AutoReplyRepository,
)
from app.schemas.wa import SessionCreate
from app.services import scope
from app.services import wa_gateway_client as gateway
from app.utils.validators import normalize_phone

logger = get_logger("wa.service")


class WaService:
    def __init__(self, db: DbSession):
        self.db = db
        self.sessions = SessionRepository(db)
        self.messages = MessageRepository(db)
        self.autoreplies = AutoReplyRepository(db)

    # ---- Sessions ----
    def create_session(self, admin: User, data: SessionCreate, supervisor_id: int | None) -> WaSession:
        """Hanya admin. `supervisor_id` = tim pemilik nomor (boleh None = belum di-assign)."""
        session_key = uuid.uuid4().hex
        wa = WaSession(
            user_id=admin.id,
            supervisor_id=supervisor_id,
            name=data.name,
            session_key=session_key,
            status="connecting",
        )
        wa = self.sessions.create(wa)
        gateway.start_session(session_key)  # minta Node mulai + generate QR
        return wa

    def list_sessions(self, actor: User) -> list[WaSession]:
        return self.sessions.list_for_team(scope.team_owner_id(actor))

    def get_visible_or_404(self, session_id: int, actor: User) -> WaSession:
        """Sesi yang boleh dilihat/dipakai actor (dalam timnya). Admin: semua."""
        wa = self.sessions.get_for_team(session_id, scope.team_owner_id(actor))
        if not wa:
            raise NotFoundError("Session tidak ditemukan")
        return wa

    def get_admin_or_404(self, session_id: int) -> WaSession:
        """Untuk operasi lifecycle (reconnect/delete/assign) — admin saja."""
        wa = self.sessions.get(session_id)
        if not wa:
            raise NotFoundError("Session tidak ditemukan")
        return wa

    def assign_team(self, wa: WaSession, supervisor_id: int | None) -> WaSession:
        wa.supervisor_id = supervisor_id
        return self.sessions.update(wa)

    def refresh_status(self, wa: WaSession) -> WaSession:
        """Tanya Node status terkini (QR/connected) lalu simpan."""
        info = gateway.get_status(wa.session_key)
        wa.status = info.get("status") or wa.status
        wa.qr = info.get("qr") or ""
        if info.get("phone"):
            wa.phone = info["phone"]
        return self.sessions.update(wa)

    def reconnect(self, wa: WaSession) -> WaSession:
        gateway.start_session(wa.session_key)
        wa.status = "connecting"
        return self.sessions.update(wa)

    def delete_session(self, wa: WaSession) -> None:
        gateway.logout(wa.session_key)
        # Bersihkan referensi dulu supaya tidak kena FK violation (Postgres
        # menegakkan foreign key; SQLite dulu tidak). Pesan inbox DIPERTAHANKAN
        # sbg riwayat (session_id di-NULL-kan), sedangkan aturan auto-reply &
        # broadcast yang terikat nomor ini ikut dihapus (tak berguna tanpa nomor).
        sid = wa.id
        self.db.query(Message).filter(Message.session_id == sid).update(
            {Message.session_id: None}, synchronize_session=False
        )
        self.db.query(AutoReply).filter(AutoReply.session_id == sid).delete(synchronize_session=False)
        self.db.query(Broadcast).filter(Broadcast.session_id == sid).delete(synchronize_session=False)
        self.db.commit()
        self.sessions.delete(wa)

    # ---- Kirim pesan + log ----
    def send(self, actor: User, session_id: int, to: str, text: str) -> Message:
        """Kirim dari salah satu anggota tim. Pesan dicatat atas nama `actor`
        supaya percakapan ini 'dimiliki' actor (regular lihat balasannya di inbox)."""
        wa = self.get_visible_or_404(session_id, actor)
        phone = normalize_phone(to)
        msg = Message(
            user_id=actor.id, session_id=wa.id, direction="out",
            chat_number=phone, body=text, status="sent",
        )
        try:
            res = gateway.send_message(wa.session_key, phone, text)
            msg.wa_message_id = res.get("id") or ""
        except Exception as e:  # noqa: BLE001 — kegagalan kirim harus tetap tercatat
            msg.status = "failed"
            msg.error = str(e)[:255]
            self.messages.create(msg)
            raise
        return self.messages.create(msg)

    def list_messages(self, actor: User, direction: str | None = None, limit: int = 100) -> list[Message]:
        return self.messages.list_scoped(scope.visible_user_ids(self.db, actor), direction, limit)

    # ---- Webhook dari Node ----
    def _team_user_ids(self, wa: WaSession) -> list[int]:
        """user_id anggota tim pemilik sesi (untuk auto-reply & fallback owner)."""
        if wa.supervisor_id:
            return scope.team_member_ids(self.db, wa.supervisor_id)
        return [wa.user_id]  # sesi belum di-assign → milik admin pembuat

    def handle_webhook(self, session_key: str, event: str, data: dict) -> None:
        wa = self.sessions.get_by_key(session_key)
        if not wa:
            logger.warning("webhook untuk session tidak dikenal: %s", session_key)
            return

        if event == "qr":
            wa.status = "qr"
            wa.qr = data.get("qr", "")
            self.sessions.update(wa)
        elif event == "connected":
            wa.status = "connected"
            wa.qr = ""
            wa.phone = data.get("phone") or wa.phone
            self.sessions.update(wa)
        elif event == "disconnected":
            wa.status = "logged_out" if data.get("loggedOut") else "disconnected"
            self.sessions.update(wa)
        elif event == "message":
            self._handle_incoming(wa, data)

    def _handle_incoming(self, wa: WaSession, data: dict) -> None:
        if data.get("fromMe"):
            return  # abaikan echo pesan kita sendiri
        number = normalize_phone(data.get("from", ""))
        body = data.get("text", "")
        # Pemilik percakapan = anggota tim yang terakhir mengirim ke nomor ini.
        # Kalau belum ada, jatuh ke pemilik tim (supervisor) / admin pembuat sesi.
        owner = self.messages.last_conversation_owner(wa.id, number)
        if owner is None:
            owner = wa.supervisor_id or wa.user_id
        self.messages.create(Message(
            user_id=owner, session_id=wa.id, direction="in",
            chat_number=number, body=body, status="received",
            wa_message_id=data.get("id", ""),
        ))
        self._maybe_auto_reply(wa, owner, number, body)

    def _maybe_auto_reply(self, wa: WaSession, owner: int, number: str, body: str) -> None:
        if not body:
            return
        text = body.strip().lower()
        for rule in self.autoreplies.list_enabled(self._team_user_ids(wa), wa.id):
            kw = rule.keyword.strip().lower()
            hit = (
                (rule.match_type == "equals" and text == kw)
                or (rule.match_type == "contains" and kw in text)
                or (rule.match_type == "starts_with" and text.startswith(kw))
            )
            if hit:
                # Kirim dengan jeda (kalau ada) — dijadwalkan biar tidak nge-block
                # webhook. Jeda meniru jeda manusia → kurangi risiko banned.
                delay = rule.delay_seconds or 0
                if delay > 0:
                    from app.services.scheduler_service import scheduler
                    scheduler.add_job(
                        _dispatch_auto_reply, "date",
                        run_date=datetime.now(timezone.utc) + timedelta(seconds=delay),
                        args=[wa.session_key, wa.id, number, rule.reply_body, owner],
                        id=f"autoreply-{wa.id}-{uuid.uuid4().hex[:8]}",
                        misfire_grace_time=120,
                    )
                else:
                    _dispatch_auto_reply(wa.session_key, wa.id, number, rule.reply_body, owner)
                break  # satu balasan per pesan masuk


def _dispatch_auto_reply(session_key: str, session_id: int, number: str, reply_body: str, owner: int) -> None:
    """Kirim balasan auto-reply + catat log. Dipakai langsung (tanpa jeda) atau
    dari scheduler (dengan jeda) — makanya buka DB session sendiri."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        res = gateway.send_message(session_key, number, reply_body)
        db.add(Message(
            user_id=owner, session_id=session_id, direction="out",
            chat_number=number, body=reply_body, status="sent",
            wa_message_id=res.get("id", ""),
        ))
        db.commit()
    except Exception as e:  # noqa: BLE001
        logger.warning("auto-reply gagal: %s", e)
    finally:
        db.close()
