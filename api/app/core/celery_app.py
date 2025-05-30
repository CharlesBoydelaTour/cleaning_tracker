from celery import Celery
from app.config import settings

celery_app = Celery(
    "cleaning_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)

# Optional: load additional config from a separate file
# celery_app.conf.update(
#     task_routes={},
#     accept_content=['json'],
#     task_serializer='json',
#     result_serializer='json'
# )
