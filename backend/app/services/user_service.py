from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.user import User, ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_USER
from app.repositories.user_repository import UserRepository
from app.schemas.user import AdminUserCreate, UserAdminUpdate, UserCreate, UserUpdate


class UserService:
    """Business logic user — bisa di-test tanpa server/DB nyata (mock repo)."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self, data: UserCreate) -> User:
        """Registrasi publik. User pertama otomatis jadi admin (bootstrap),
        sisanya jadi regular user tanpa tim (harus di-assign admin)."""
        if self.repo.get_by_email(data.email):
            raise ConflictError("Email sudah terdaftar")
        is_first = not self.repo.list_all()  # user pertama = admin (bootstrap)
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=ROLE_ADMIN if is_first else ROLE_USER,
        )
        return self.repo.create(user)

    def get_user(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("User tidak ditemukan")
        return user

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.get_user(user_id)
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        return self.repo.update(user)

    # --- Manajemen user (admin / supervisor) ---
    def _validate_supervisor(self, supervisor_id: int) -> None:
        sup = self.repo.get(supervisor_id)
        if not sup or sup.role != ROLE_SUPERVISOR:
            raise NotFoundError("Supervisor tidak valid")

    def create_managed(self, data: AdminUserCreate) -> User:
        """Admin membuat user role apa pun."""
        if self.repo.get_by_email(data.email):
            raise ConflictError("Email sudah terdaftar")
        supervisor_id = None
        if data.role == ROLE_USER:
            if not data.supervisor_id:
                raise ForbiddenError("Regular user wajib punya supervisor")
            self._validate_supervisor(data.supervisor_id)
            supervisor_id = data.supervisor_id
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            supervisor_id=supervisor_id,
        )
        return self.repo.create(user)

    def create_regular_for(self, supervisor: User, email: str, password: str, full_name: str) -> User:
        """Supervisor membuat regular user untuk timnya sendiri."""
        if self.repo.get_by_email(email):
            raise ConflictError("Email sudah terdaftar")
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=ROLE_USER,
            supervisor_id=supervisor.id,
        )
        return self.repo.create(user)

    def admin_update(self, user_id: int, data: UserAdminUpdate) -> User:
        user = self.get_user(user_id)
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.role is not None:
            user.role = data.role
            if data.role != ROLE_USER:
                user.supervisor_id = None  # admin/supervisor tak punya atasan tim
        if data.supervisor_id is not None and user.role == ROLE_USER:
            self._validate_supervisor(data.supervisor_id)
            user.supervisor_id = data.supervisor_id
        return self.repo.update(user)

    def list_for(self, actor: User) -> list[User]:
        """Admin lihat semua user; supervisor lihat timnya."""
        if actor.role == ROLE_ADMIN:
            return self.repo.list_all()
        if actor.role == ROLE_SUPERVISOR:
            return self.repo.list_team(actor.id)
        return [actor]
