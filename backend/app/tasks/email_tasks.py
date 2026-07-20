"""Background jobs — ganti dengan Celery/APScheduler/ARQ sesuai kebutuhan project."""
from app.core.logging import get_logger

logger = get_logger("tasks")


def send_welcome_email(email: str) -> None:
    # Stub: integrasikan dengan SMTP/SendGrid/SES di sini
    logger.info("Queued welcome email untuk %s", email)
