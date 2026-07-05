from celery import Celery
from celery.signals import setup_logging, worker_process_init

from src.config import get_settings
from src.shared.logging import configure_logging

_settings = get_settings()


@setup_logging.connect
def _skip_celery_logging(**_kwargs: object) -> None:
    """Stop Celery from installing its own root logging config — we route
    everything through loguru instead (connecting to this signal at all
    disables Celery's default handler setup)."""
    configure_logging()


@worker_process_init.connect
def _init_worker_logging(**_kwargs: object) -> None:
    """Each forked worker process gets its own loguru sink — signals fire
    per-process, so configuring here (not just at import) covers the pool."""
    configure_logging()

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
