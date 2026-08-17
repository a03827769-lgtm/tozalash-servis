from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tozalash_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
)

# Optional: Celery Beat for Scheduled Tasks
celery_app.conf.beat_schedule = {
    # 'send-monthly-reports': {
    #     'task': 'app.workers.tasks.generate_monthly_reports',
    #     'schedule': crontab(day_of_month='1', hour=0, minute=0),
    # },
}
