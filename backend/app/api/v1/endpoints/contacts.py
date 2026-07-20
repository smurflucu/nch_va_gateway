from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_supervisor_or_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.models.wa import Contact
from app.repositories.wa_repository import ContactRepository
from app.schemas.wa import ContactCreate, ContactRead
from app.services import scope
from app.utils.validators import normalize_phone

router = APIRouter(prefix="/contacts", tags=["wa-contacts"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ContactRead])
def list_contacts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Kontak level-tim: regular ikut lihat (read-only), supervisor/admin kelola.
    return ContactRepository(db).list_scoped(scope.team_scope_ids(db, user))


@router.post("", response_model=ContactRead, status_code=201)
def create_contact(
    data: ContactCreate,
    user: User = Depends(require_supervisor_or_admin),  # regular tidak boleh kelola kontak
    db: Session = Depends(get_db),
):
    repo = ContactRepository(db)
    phone = normalize_phone(data.phone)
    if repo.find_by_phone_scoped(scope.team_scope_ids(db, user), phone):
        raise ConflictError("Kontak dengan nomor itu sudah ada di tim")
    return repo.create(Contact(user_id=user.id, name=data.name, phone=phone, tags=data.tags))


@router.delete("/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    user: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    repo = ContactRepository(db)
    c = repo.get_scoped(contact_id, scope.team_scope_ids(db, user))
    if not c:
        raise NotFoundError("Kontak tidak ditemukan")
    repo.delete(c)
