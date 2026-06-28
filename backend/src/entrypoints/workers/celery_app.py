from celery import Celery

from src.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "parallax",
    broker=_settings.CELERY_BROKER_URL,
    backend=_settings.CELERY_RESULT_BACKEND,
    include=[
        "src.entrypoints.workers.intake_consumer",
        "src.entrypoints.workers.ingestion_consumer",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
