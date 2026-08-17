from celery.utils.log import get_task_logger
from app.workers.celery_app import celery_app
import time

logger = get_task_logger(__name__)


@celery_app.task(name="send_email_notification")
def send_email_notification(to_email: str, subject: str, body: str):
    logger.info(f"Sending email to {to_email}...")
    # Simulate email sending
    time.sleep(2)
    logger.info(f"Email sent successfully to {to_email}")
    return True


@celery_app.task(name="process_ai_analytics")
def process_ai_analytics():
    logger.info("Starting AI analytics processing...")
    # Insert AI analytics logic here
    time.sleep(5)
    logger.info("AI analytics processed successfully.")
    return True
