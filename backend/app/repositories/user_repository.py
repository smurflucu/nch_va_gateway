from sqlalchemy.orm import Session
from app.models.user import User, ROLE_SUPERVISOR
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def list_all(self) -> list[User]:
        return self.db.query(User).order_by(User.role, User.full_name).all()

    def list_team(self, supervisor_id: int) -> list[User]:
        """Supervisor + regular user di bawahnya."""
        return (
            self.db.query(User)
            .filter((User.id == supervisor_id) | (User.supervisor_id == supervisor_id))
            .order_by(User.role, User.full_name)
            .all()
        )

    def list_supervisors(self) -> list[User]:
        return self.db.query(User).filter(User.role == ROLE_SUPERVISOR).order_by(User.full_name).all()
