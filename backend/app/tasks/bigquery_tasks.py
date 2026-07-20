"""Template task BigQuery + alert Google Chat.
Butuh: pip install google-cloud-bigquery, dan service account
(GOOGLE_APPLICATION_CREDENTIALS) di environment.
Ganti project/dataset/SP sesuai kebutuhan."""
import requests
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("tasks.bq")

# Ganti sesuai project lo
BQ_PROJECT = "your-project"
SP_DAILY = f"CALL `{BQ_PROJECT}.your_dataset.sp_daily_recon`()"
RECON_CHECK_SQL = f"""
SELECT COUNT(*) AS anomali
FROM `{BQ_PROJECT}.your_dataset.v_double_settlement`
WHERE DATE(created_at) = CURRENT_DATE('Asia/Jakarta')
"""


def send_chat_alert(message: str) -> None:
    """Kirim pesan ke Google Chat webhook (kalau diset di .env)."""
    if not settings.GOOGLE_CHAT_WEBHOOK:
        logger.warning("GOOGLE_CHAT_WEBHOOK kosong, skip alert: %s", message)
        return
    requests.post(settings.GOOGLE_CHAT_WEBHOOK, json={"text": message}, timeout=10)


def call_stored_procedure() -> str:
    """Template: panggil stored procedure BigQuery (pengganti scheduled query)."""
    from google.cloud import bigquery  # import di dalam supaya app tetap jalan tanpa lib ini

    client = bigquery.Client(project=BQ_PROJECT)
    job = client.query(SP_DAILY)
    job.result()  # tunggu selesai; raise exception kalau gagal -> tercatat failed di history
    return f"SP selesai, job_id={job.job_id}"


def recon_check_and_alert() -> str:
    """Template: cek anomali recon, alert ke Google Chat kalau ketemu."""
    from google.cloud import bigquery

    client = bigquery.Client(project=BQ_PROJECT)
    rows = list(client.query(RECON_CHECK_SQL).result())
    anomali = rows[0]["anomali"] if rows else 0
    if anomali > 0:
        send_chat_alert(f"⚠️ Recon alert: {anomali} transaksi double settlement terdeteksi hari ini!")
        return f"ALERT: {anomali} anomali"
    return "clean: 0 anomali"
