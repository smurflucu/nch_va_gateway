from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

# Peran (role) yang valid. Hirarki: admin > supervisor > user (regular).
ROLE_ADMIN = "admin"
ROLE_SUPERVISOR = "supervisor"
ROLE_USER = "user"
VALID_ROLES = {ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_USER}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=ROLE_USER)  # admin|supervisor|user
    # Untuk regular user: id supervisor pemilik timnya. NULL untuk admin & supervisor.
    # "Tim" = satu supervisor + semua regular user yang supervisor_id-nya menunjuk ke dia.
    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
