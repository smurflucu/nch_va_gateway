from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_supervisor_or_admin
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wa import AutoReply
from app.repositories.wa_repository import AutoReplyRepository
from app.schemas.wa import AutoReplyCreate, AutoReplyUpdate, AutoReplyRead
from app.services import scope

router = APIRouter(prefix="/autoreplies", tags=["wa-autoreplies"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AutoReplyRead])
def list_rules(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AutoReplyRepository(db).list_scoped(scope.team_scope_ids(db, user))


@router.post("", response_model=AutoReplyRead, status_code=201)
def create_rule(
    data: AutoReplyCreate,
    user: User = Depends(require_supervisor_or_admin),  # aturan auto-reply level tim
    db: Session = Depends(get_db),
):
    repo = AutoReplyRepository(db)
    return repo.create(AutoReply(user_id=user.id, **data.model_dump()))


@router.patch("/{rule_id}", response_model=AutoReplyRead)
def update_rule(
    rule_id: int,
    data: AutoReplyUpdate,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    repo = AutoReplyRepository(db)
    rule = repo.get_scoped(rule_id, scope.team_scope_ids(db, user))
    if not rule:
        raise NotFoundError("Aturan tidak ditemukan")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    return repo.update(rule)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    repo = AutoReplyRepository(db)
    rule = repo.get_scoped(rule_id, scope.team_scope_ids(db, user))
    if not rule:
        raise NotFoundError("Aturan tidak ditemukan")
    repo.delete(rule)
