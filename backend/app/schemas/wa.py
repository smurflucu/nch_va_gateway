from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ---------- Sessions ----------
class SessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    supervisor_id: int | None = None  # tim pemilik nomor (admin yang tentukan)


class SessionAssign(BaseModel):
    supervisor_id: int | None = None  # pindah/lepas kepemilikan tim


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    session_key: str
    status: str
    phone: str
    supervisor_id: int | None = None
    created_at: datetime


class SessionStatus(BaseModel):
    id: int
    status: str
    phone: str
    qr: str  # data URL (kosong kalau tidak ada)


# ---------- Contacts ----------
class ContactCreate(BaseModel):
    name: str = Field(default="", max_length=120)
    phone: str = Field(min_length=6, max_length=30)
    tags: str = Field(default="", max_length=255)


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str
    tags: str
    created_at: datetime


# ---------- Templates ----------
class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1)


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    body: str
    created_at: datetime


# ---------- Messages / send ----------
class SendMessage(BaseModel):
    session_id: int
    to: str = Field(min_length=6, max_length=30)
    text: str = Field(min_length=1)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int | None
    direction: str
    chat_number: str
    body: str
    status: str
    error: str
    created_at: datetime


# ---------- Auto reply ----------
class AutoReplyCreate(BaseModel):
    session_id: int | None = None
    match_type: str = Field(default="contains", pattern="^(equals|contains|starts_with)$")
    keyword: str = Field(min_length=1, max_length=255)
    reply_body: str = Field(min_length=1)
    delay_seconds: int = Field(default=0, ge=0, le=300)  # jeda sebelum balas (anti-ban)
    enabled: bool = True


class AutoReplyUpdate(BaseModel):
    match_type: str | None = Field(default=None, pattern="^(equals|contains|starts_with)$")
    keyword: str | None = Field(default=None, max_length=255)
    reply_body: str | None = None
    delay_seconds: int | None = Field(default=None, ge=0, le=300)
    enabled: bool | None = None


class AutoReplyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int | None
    match_type: str
    keyword: str
    reply_body: str
    delay_seconds: int
    enabled: bool
    created_at: datetime


# ---------- API keys ----------
class ApiKeyCreate(BaseModel):
    name: str = Field(default="", max_length=120)


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    prefix: str
    enabled: bool
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyCreated(ApiKeyRead):
    key: str  # HANYA muncul sekali saat pembuatan


# ---------- Broadcast ----------
class BroadcastTarget(BaseModel):
    phone: str
    name: str = ""


class BroadcastCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    session_id: int
    body: str = Field(min_length=1)
    targets: list[BroadcastTarget] = Field(min_length=1)
    delay_seconds: int = Field(default=5, ge=0, le=120)
    scheduled_at: datetime | None = None  # kalau diisi -> dijalankan scheduler


class BroadcastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    session_id: int
    body: str
    status: str
    approved_by: int | None = None
    delay_seconds: int
    scheduled_at: datetime | None
    total: int
    sent: int
    failed: int
    created_at: datetime


# ---------- Gateway (API-key) ----------
class GatewaySend(BaseModel):
    session_id: int
    to: str = Field(min_length=6, max_length=30)
    text: str = Field(min_length=1)


# ---------- Webhook dari Node ----------
class WebhookEvent(BaseModel):
    sessionKey: str
    event: str  # qr|connected|disconnected|message
    data: dict
