from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.wa import SessionAssign, SessionCreate, SessionRead, SessionStatus
from app.services.wa_service import WaService

router = APIRouter(prefix="/sessions", tags=["wa-sessions"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SessionRead])
def list_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Nomor tim yang boleh dilihat user (admin: semua)."""
    return WaService(db).list_sessions(user)


@router.post("", response_model=SessionRead, status_code=201)
def create_session(
    data: SessionCreate,
    admin: User = Depends(require_admin),  # HANYA admin yang input nomor
    db: Session = Depends(get_db),
):
    return WaService(db).create_session(admin, data, data.supervisor_id)


@router.patch("/{session_id}/assign", response_model=SessionRead)
def assign_session(
    session_id: int,
    data: SessionAssign,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin assign / pindah nomor ke supervisor (tim)."""
    svc = WaService(db)
    return svc.assign_team(svc.get_admin_or_404(session_id), data.supervisor_id)


@router.get("/{session_id}/status", response_model=SessionStatus)
def session_status(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = WaService(db)
    wa = svc.get_visible_or_404(session_id, user)
    wa = svc.refresh_status(wa)
    return SessionStatus(id=wa.id, status=wa.status, phone=wa.phone, qr=wa.qr)


@router.post("/{session_id}/reconnect", response_model=SessionRead)
def reconnect(session_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    svc = WaService(db)
    return svc.reconnect(svc.get_admin_or_404(session_id))


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    svc = WaService(db)
    svc.delete_session(svc.get_admin_or_404(session_id))
