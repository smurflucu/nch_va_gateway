from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.wa import SendMessage, MessageRead
from app.services.wa_service import WaService

router = APIRouter(prefix="/messages", tags=["wa-messages"], dependencies=[Depends(get_current_user)])


@router.post("/send", response_model=MessageRead, status_code=201)
def send(data: SendMessage, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Semua role boleh kirim (nomor timnya). Scope dicek di service.
    return WaService(db).send(user, data.session_id, data.to, data.text)


@router.get("", response_model=list[MessageRead])
def list_messages(
    direction: str | None = Query(default=None, pattern="^(in|out)$"),
    limit: int = Query(default=100, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Regular: inbox miliknya. Supervisor: seluruh tim. Admin: semua.
    return WaService(db).list_messages(user, direction=direction, limit=limit)
