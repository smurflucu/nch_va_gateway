from fastapi import APIRouter, Depends
from app.api.deps import (
    get_current_user,
    get_user_service,
    require_admin,
    require_supervisor_or_admin,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User, ROLE_SUPERVISOR
from app.schemas.user import (
    AdminUserCreate,
    SupervisorRegularCreate,
    UserAdminUpdate,
    UserRead,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserRead)
def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return service.update_user(user.id, data)


# --- Manajemen tim / user ---
@router.get("", response_model=list[UserRead])
def list_users(
    actor: User = Depends(require_supervisor_or_admin),
    service: UserService = Depends(get_user_service),
):
    """Admin: semua user. Supervisor: tim sendiri."""
    return service.list_for(actor)


@router.get("/supervisors", response_model=list[UserRead])
def list_supervisors(
    _: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Daftar supervisor (untuk assign regular user & assign nomor WA)."""
    return service.repo.list_supervisors()


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    data: AdminUserCreate,
    _: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Admin membuat user role apa pun (admin/supervisor/regular)."""
    return service.create_managed(data)


@router.post("/team", response_model=UserRead, status_code=201)
def create_team_member(
    data: SupervisorRegularCreate,
    actor: User = Depends(require_supervisor_or_admin),
    service: UserService = Depends(get_user_service),
):
    """Supervisor membuat regular user untuk timnya sendiri."""
    if actor.role != ROLE_SUPERVISOR:
        raise ForbiddenError("Hanya supervisor yang bisa menambah anggota tim di sini")
    return service.create_regular_for(actor, data.email, data.password, data.full_name)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    _: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Admin ubah role / supervisor / status aktif user."""
    return service.admin_update(user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    actor: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    if user_id == actor.id:
        raise ForbiddenError("Tidak bisa menghapus akun sendiri")
    user = service.repo.get(user_id)
    if not user:
        raise NotFoundError("User tidak ditemukan")
    service.repo.delete(user)
