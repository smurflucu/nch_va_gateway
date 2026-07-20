"""Registry: nama task -> fungsi Python.
Semua fungsi yang mau bisa dijadwalkan HARUS didaftarkan di sini.
Fungsi boleh return string (dicatat sebagai output di history)."""
from app.tasks import demo_tasks, bigquery_tasks, broadcast_tasks

TASK_REGISTRY: dict[str, callable] = {
    "heartbeat": demo_tasks.heartbeat,
    "cleanup_old_job_runs": demo_tasks.cleanup_old_job_runs,
    "bq_call_stored_procedure": bigquery_tasks.call_stored_procedure,
    "bq_recon_check_and_alert": bigquery_tasks.recon_check_and_alert,
    "dispatch_due_broadcasts": broadcast_tasks.dispatch_due_broadcasts,
}
