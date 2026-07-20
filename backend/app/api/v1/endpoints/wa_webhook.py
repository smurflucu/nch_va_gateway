"""Terima event dari service Node (Baileys): qr, connected, disconnected, message.
Diproteksi shared secret — BUKAN endpoint publik. Hanya Node yang tahu secretnya."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.schemas.wa import WebhookEvent
from app.services.wa_service import WaService

router = APIRouter(prefix="/wa", tags=["wa-webhook"])


@router.post("/webhook", status_code=204)
def webhook(
    payload: WebhookEvent,
    db: Session = Depends(get_db),
    x_webhook_secret: str = Header(default=""),
):
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise UnauthorizedError("Webhook secret salah")
    WaService(db).handle_webhook(payload.sessionKey, payload.event, payload.data)
