"""Semua model domain WhatsApp gateway — semuanya di-scope ke user_id (multi-tenant)."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def _now():
    return datetime.now(timezone.utc)


class WaSession(Base):
    """Satu baris = satu nomor/perangkat WhatsApp milik seorang user."""
    __tablename__ = "wa_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # admin pembuat
    # Tim pemilik nomor ini (= id supervisor). Hanya admin yang input & assign nomor.
    # Supervisor + regular di timnya boleh memakai nomor ini; tim lain tidak.
    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    session_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # id di Node gateway
    status: Mapped[str] = mapped_column(String(20), default="disconnected")  # disconnected|qr|connected|logged_out
    phone: Mapped[str] = mapped_column(String(30), default="")
    qr: Mapped[str] = mapped_column(Text, default="")  # data URL QR terakhir
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Contact(Base):
    __tablename__ = "wa_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(30), nullable=False)  # sudah ternormalisasi 62xxx
    tags: Mapped[str] = mapped_column(String(255), default="")  # dipisah koma
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class MessageTemplate(Base):
    __tablename__ = "wa_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)  # boleh pakai {{name}}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Message(Base):
    """Log pesan masuk & keluar (inbox + outbox)."""
    __tablename__ = "wa_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("wa_sessions.id"), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(10))  # in | out
    chat_number: Mapped[str] = mapped_column(String(30), index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(15), default="sent")  # received|sent|failed
    wa_message_id: Mapped[str] = mapped_column(String(64), default="")
    error: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class AutoReply(Base):
    __tablename__ = "wa_autoreplies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("wa_sessions.id"), nullable=True)  # null = semua sesi
    match_type: Mapped[str] = mapped_column(String(15), default="contains")  # equals|contains|starts_with
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    reply_body: Mapped[str] = mapped_column(Text, nullable=False)
    # Jeda (detik) sebelum balasan dikirim — meniru jeda manusia, kurangi risiko banned.
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ApiKey(Base):
    """Kunci untuk aplikasi eksternal kirim pesan lewat /gateway/send."""
    __tablename__ = "wa_api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    prefix: Mapped[str] = mapped_column(String(12), index=True)  # 8 char pertama, buat tampil & lookup
    key_hash: Mapped[str] = mapped_column(String(255))           # sisanya di-hash (bcrypt)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Broadcast(Base):
    __tablename__ = "wa_broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # pembuat broadcast
    session_id: Mapped[int] = mapped_column(ForeignKey("wa_sessions.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    targets: Mapped[str] = mapped_column(Text, default="")  # JSON: [{"phone": "...", "name": "..."}]
    delay_seconds: Mapped[int] = mapped_column(Integer, default=5)  # jeda antar pesan (anti-ban)
    # draft|pending_approval|scheduled|running|done|failed|rejected
    # Broadcast dibuat regular user -> pending_approval (butuh acc supervisor/admin).
    status: Mapped[str] = mapped_column(String(20), default="draft")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
