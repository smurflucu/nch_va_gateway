from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class ScheduledJob(Base):
    """Definisi job — pengganti baris crontab."""
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)  # key di tasks/registry.py
    cron: Mapped[str] = mapped_column(String(100), nullable=False)       # ex: "0 6 * * *"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class JobRun(Base):
    """History eksekusi — pengganti grep syslog."""
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("scheduled_jobs.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(20), default="schedule")  # schedule | manual
    status: Mapped[str] = mapped_column(String(20), default="running")    # running | success | failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output: Mapped[str] = mapped_column(Text, default="")   # return value / error message
