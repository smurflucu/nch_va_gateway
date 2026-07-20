from sqlalchemy.orm import Session
from app.models.job import ScheduledJob, JobRun
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[ScheduledJob]):
    def __init__(self, db: Session):
        super().__init__(ScheduledJob, db)

    def get_by_name(self, name: str) -> ScheduledJob | None:
        return self.db.query(ScheduledJob).filter(ScheduledJob.name == name).first()

    def list_runs(self, job_id: int, limit: int = 50) -> list[JobRun]:
        return (
            self.db.query(JobRun)
            .filter(JobRun.job_id == job_id)
            .order_by(JobRun.started_at.desc())
            .limit(limit)
            .all()
        )
