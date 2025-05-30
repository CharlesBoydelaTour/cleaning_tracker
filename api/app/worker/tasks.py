from app.core.celery_app import celery_app


@celery_app.task
def send_notification(email: str, message: str):
    # TODO: implémenter l'envoi de notification
    print(f"Sending notification to {email}: {message}")
