from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_supervisor_or_admin
from app.models.user import User
from app.schemas.wa import BroadcastCreate, BroadcastRead
from app.services.broadcast_service import BroadcastService

router = APIRouter(prefix="/broadcasts", tags=["wa-broadcasts"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[BroadcastRead])
def list_broadcasts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Regular: miliknya. Supervisor: tim. Admin: semua.
    return BroadcastService(db).list_for(user)


@router.get("/pending", response_model=list[BroadcastRead])
def list_pending(user: User = Depends(require_supervisor_or_admin), db: Session = Depends(get_db)):
    """Antrian broadcast menunggu approval (untuk supervisor/admin)."""
    return BroadcastService(db).list_pending(user)


@router.post("", response_model=BroadcastRead, status_code=201)
def create_broadcast(data: BroadcastCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Regular user -> otomatis pending_approval (lihat BroadcastService.create).
    return BroadcastService(db).create(user, data)


@router.get("/{broadcast_id}", response_model=BroadcastRead)
def get_broadcast(broadcast_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return BroadcastService(db).get_or_404(user, broadcast_id)


@router.post("/{broadcast_id}/approve", response_model=BroadcastRead)
def approve_broadcast(
    broadcast_id: int,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    return BroadcastService(db).approve(user, broadcast_id)


@router.post("/{broadcast_id}/reject", response_model=BroadcastRead)
def reject_broadcast(
    broadcast_id: int,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    return BroadcastService(db).reject(user, broadcast_id)
