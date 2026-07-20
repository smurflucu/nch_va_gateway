"""Endpoint publik untuk aplikasi eksternal — auth pakai header X-API-Key.
Contoh:
    curl -X POST https://host/api/v1/gateway/send \\
      -H "X-API-Key: wa_xxx_yyy" -H "Content-Type: application/json" \\
      -d '{"session_id": 1, "to": "0812xxxx", "text": "Halo"}'
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_apikey_user, get_db
from app.core.config import settings
from app.middlewares.rate_limit import limiter
from app.models.user import User
from app.schemas.wa import GatewaySend, MessageRead
from app.services.wa_service import WaService

router = APIRouter(prefix="/gateway", tags=["wa-gateway"])


@router.post("/send", response_model=MessageRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def gateway_send(
    request: Request,
    data: GatewaySend,
    user: User = Depends(get_apikey_user),
    db: Session = Depends(get_db),
):
    # Kirim atas nama pemilik API-key (di-scope timnya di dalam service).
    return WaService(db).send(user, data.session_id, data.to, data.text)
