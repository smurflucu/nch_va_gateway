"""Jantung pengganti crontab.
- Baca definisi job dari DB waktu startup, daftarkan ke APScheduler
- Setiap run tercatat di job_runs (status, durasi, output/error)
- Job gagal -> alert Google Chat (kalau webhook diset)
- max_instances=1: job yang masih jalan tidak akan dobel"""
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.job import ScheduledJob, JobRun
from app.tasks.registry import TASK_REGISTRY

logger = get_logger("scheduler")

scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)


def _validate_cron(cron: str) -> CronTrigger:
    try:
        return CronTrigger.from_crontab(cron, timezone=settings.SCHEDULER_TIMEZONE)
    except ValueError as e:
        raise AppException(f"Cron expression invalid: {e}", 422)


def _execute(job_id: int, trigger: str = "schedule") -> None:
    """Wrapper eksekusi: catat history, jalankan task, catat hasil."""
    db = SessionLocal()
    try:
        job = db.get(ScheduledJob, job_id)
        if not job:
            return
        func = TASK_REGISTRY.get(job.task_name)
        run = JobRun(job_id=job.id, trigger=trigger)
        db.add(run)
        db.commit()
        db.refresh(run)

        start = datetime.now(timezone.utc)
        try:
            if func is None:
                raise RuntimeError(f"Task '{job.task_name}' tidak ada di registry")
            result = func()
            run.status = "success"
            run.output = str(result) if result is not None else ""
        except Exception as e:  # noqa: BLE001 — semua error harus tercatat
            run.status = "failed"
            run.output = f"{type(e).__name__}: {e}"
            logger.exception("Job '%s' gagal", job.name)
            _alert_failure(job.name, run.output)
        finally:
            end = datetime.now(timezone.utc)
            run.finished_at = end
            run.duration_ms = int((end - start).total_seconds() * 1000)
            db.commit()
    finally:
        db.close()


def _alert_failure(job_name: str, error: str) -> None:
    try:
        from app.tasks.bigquery_tasks import send_chat_alert
        send_chat_alert(f"🔴 Job *{job_name}* GAGAL:\n```{error[:500]}```")
    except Exception:  # noqa: BLE001 — alert gagal jangan bikin crash
        logger.warning("Gagal kirim alert untuk job %s", job_name)


def _aps_id(job_id: int) -> str:
    return f"job-{job_id}"


def register_job(job: ScheduledJob) -> None:
    """Daftarkan/refresh satu job di scheduler."""
    aps_id = _aps_id(job.id)
    if scheduler.get_job(aps_id):
        scheduler.remove_job(aps_id)
    if job.enabled:
        scheduler.add_job(
            _execute,
            trigger=_validate_cron(job.cron),
            args=[job.id],
            id=aps_id,
            name=job.name,
            max_instances=1,
            coalesce=True,        # kalau ketinggalan beberapa jadwal, jalankan sekali saja
            misfire_grace_time=300,
        )


def unregister_job(job_id: int) -> None:
    aps_id = _aps_id(job_id)
    if scheduler.get_job(aps_id):
        scheduler.remove_job(aps_id)


def run_now(job_id: int) -> None:
    """Trigger manual — jalan di thread scheduler, non-blocking untuk API."""
    scheduler.add_job(
        _execute,
        args=[job_id, "manual"],
        id=f"manual-{job_id}-{datetime.now(timezone.utc).timestamp()}",
        max_instances=1,
    )


def get_next_run(job_id: int) -> datetime | None:
    aps_job = scheduler.get_job(_aps_id(job_id))
    return aps_job.next_run_time if aps_job else None


def seed_default_jobs(db) -> None:
    """Isi contoh job kalau tabel masih kosong — biar dashboard langsung ada isinya."""
    if db.query(ScheduledJob).count() > 0:
        return
    defaults = [
        ScheduledJob(name="heartbeat", task_name="heartbeat", cron="*/5 * * * *",
                     description="Demo: log heartbeat tiap 5 menit", enabled=True),
        ScheduledJob(name="cleanup-job-history", task_name="cleanup_old_job_runs", cron="0 2 * * *",
                     description="Hapus history run > 30 hari, tiap jam 2 pagi", enabled=True),
        ScheduledJob(name="bq-daily-recon", task_name="bq_call_stored_procedure", cron="0 6 * * *",
                     description="Template: panggil SP BigQuery jam 6 pagi (edit bigquery_tasks.py dulu)",
                     enabled=False),
        ScheduledJob(name="bq-double-settlement-check", task_name="bq_recon_check_and_alert", cron="30 * * * *",
                     description="Template: cek anomali + alert Google Chat (edit dulu)", enabled=False),
        ScheduledJob(name="dispatch-broadcasts", task_name="dispatch_due_broadcasts", cron="* * * * *",
                     description="Jalankan broadcast WA terjadwal yang waktunya tiba (tiap menit)", enabled=True),
    ]
    db.add_all(defaults)
    db.commit()


def start_scheduler() -> None:
    """Panggil sekali waktu app startup."""
    db = SessionLocal()
    try:
        seed_default_jobs(db)
        for job in db.query(ScheduledJob).all():
            try:
                register_job(job)
            except AppException as e:
                logger.error("Skip job '%s': %s", job.name, e.message)
    finally:
        db.close()
    scheduler.start()
    logger.info("Scheduler aktif (%s), %d job terdaftar",
                settings.SCHEDULER_TIMEZONE, len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
