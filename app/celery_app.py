from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "flornya",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL,
    include=[
        "app.tasks.reminder_tasks",
        "app.tasks.account_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=settings.CELERY_BROKER_URL,
    beat_schedule={
        "period-reminders": {
            "task": "app.tasks.reminder_tasks.send_period_reminders",
            "schedule": crontab(minute=0),
        },
        "medication-reminders": {
            "task": "app.tasks.reminder_tasks.send_medication_reminders",
            "schedule": crontab(minute=0),
        },
        "hydration-reminders": {
            "task": "app.tasks.reminder_tasks.send_hydration_reminders",
            "schedule": crontab(minute=0, hour="8,11,14,17,20"),
        },
        "mood-checkin-reminders": {
            "task": "app.tasks.reminder_tasks.send_mood_checkin_reminders",
            "schedule": crontab(minute=0),
        },
        "anonymize-deletions": {
            "task": "app.tasks.account_tasks.anonymize_pending_deletions",
            "schedule": crontab(minute=0, hour=3),
        },
        "pregnancy-appointment-reminders": {
            "task": "app.tasks.reminder_tasks.send_pregnancy_appointment_reminders",
            "schedule": crontab(minute=0, hour=8),
        },
    },
)
