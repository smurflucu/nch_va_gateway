from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictError, NotFoundError, AppException
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobUpdate, JobRead, JobRunRead
from app.services import scheduler_service
from app.tasks.registry import TASK_REGISTRY

# Semua endpoint jobs butuh login
router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(get_current_user)])


def _to_read(job) -> JobRead:
    data = JobRead.model_validate(job)
    data.next_run = scheduler_service.get_next_run(job.id)
    return data


@router.get("/tasks")
def list_available_tasks():
    """Task yang tersedia di registry — pilihan waktu bikin job baru."""
    return sorted(TASK_REGISTRY.keys())


@router.get("", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    repo = JobRepository(db)
    return [_to_read(j) for j in repo.list(limit=200)]


@router.post("", response_model=JobRead, status_code=201)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    if repo.get_by_name(data.name):
        raise ConflictError(f"Job '{data.name}' sudah ada")
    if data.task_name not in TASK_REGISTRY:
        raise AppException(f"Task '{data.task_name}' tidak ada di registry", 422)
    scheduler_service._validate_cron(data.cron)  # validasi sebelum simpan

    from app.models.job import ScheduledJob
    job = repo.create(ScheduledJob(**data.model_dump()))
    scheduler_service.register_job(job)
    return _to_read(job)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: int, data: JobUpdate, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise NotFoundError("Job tidak ditemukan")
    if data.cron is not None:
        scheduler_service._validate_cron(data.cron)
        job.cron = data.cron
    if data.enabled is not None:
        job.enabled = data.enabled
    if data.description is not None:
        job.description = data.description
    job = repo.update(job)
    scheduler_service.register_job(job)  # reschedule langsung, tanpa restart
    return _to_read(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise NotFoundError("Job tidak ditemukan")
    scheduler_service.unregister_job(job.id)
    repo.delete(job)


@router.post("/{job_id}/run", status_code=202)
def run_job_now(job_id: int, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    if not repo.get(job_id):
        raise NotFoundError("Job tidak ditemukan")
    scheduler_service.run_now(job_id)
    return {"detail": "Job dijalankan di background — cek history"}


@router.get("/{job_id}/runs", response_model=list[JobRunRead])
def job_history(job_id: int, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    if not repo.get(job_id):
        raise NotFoundError("Job tidak ditemukan")
    return repo.list_runs(job_id)
