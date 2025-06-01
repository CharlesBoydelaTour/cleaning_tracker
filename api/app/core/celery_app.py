from celery import Celery
from celery.schedules import crontab  # AJOUTER cet import
from app.config import settings

celery_app = Celery(
    "cleaning_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)

# Configuration pour l'autodiscovery des tâches
celery_app.conf.update(
    imports=['app.worker.tasks'],  # Import explicite
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# AJOUTER cette configuration après la création de celery_app
celery_app.conf.beat_schedule = {
    # Rappels quotidiens à 8h
    'send-daily-reminders': {
        'task': 'send_daily_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Traiter la queue toutes les 5 minutes
    'process-notification-queue': {
        'task': 'process_notification_queue',
        'schedule': crontab(minute='*/5'),
    },
    # Vérifier les tâches en retard toutes les heures
    'check-overdue-tasks': {
        'task': 'check_overdue_tasks',
        'schedule': crontab(minute=0),  # Toutes les heures
    },
}

celery_app.conf.timezone = 'UTC'