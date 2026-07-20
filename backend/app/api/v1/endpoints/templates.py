from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_supervisor_or_admin
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wa import MessageTemplate
from app.repositories.wa_repository import TemplateRepository
from app.schemas.wa import TemplateCreate, TemplateRead
from app.services import scope

router = APIRouter(prefix="/templates", tags=["wa-templates"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[TemplateRead])
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return TemplateRepository(db).list_scoped(scope.team_scope_ids(db, user))


@router.post("", response_model=TemplateRead, status_code=201)
def create_template(
    data: TemplateCreate,
    user: User = Depends(require_supervisor_or_admin),  # regular read-only
    db: Session = Depends(get_db),
):
    repo = TemplateRepository(db)
    return repo.create(MessageTemplate(user_id=user.id, name=data.name, body=data.body))


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    repo = TemplateRepository(db)
    t = repo.get_scoped(template_id, scope.team_scope_ids(db, user))
    if not t:
        raise NotFoundError("Template tidak ditemukan")
    repo.delete(t)
