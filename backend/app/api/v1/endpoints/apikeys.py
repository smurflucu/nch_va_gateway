from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.wa_repository import ApiKeyRepository
from app.schemas.wa import ApiKeyCreate, ApiKeyRead, ApiKeyCreated  # noqa: F401
from app.services.apikey_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["wa-apikeys"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ApiKeyRead])
def list_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiKeyRepository(db).list_for_user(user.id)


@router.post("", response_model=ApiKeyCreated, status_code=201)
def create_key(data: ApiKeyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj, full_key = ApiKeyService(db).create(user.id, data.name)
    # key hanya ditampilkan sekali ini — setelah ini cuma prefix yang tersimpan
    return ApiKeyCreated(**ApiKeyRead.model_validate(obj).model_dump(), key=full_key)


@router.delete("/{key_id}", status_code=204)
def delete_key(key_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    key = repo.get_owned(key_id, user.id)
    if not key:
        raise NotFoundError("API key tidak ditemukan")
    repo.delete(key)
