import logging
import sys
from types import FrameType

from loguru import logger

from src.config import get_settings

# Stdlib loggers that spam INFO lines with no domain value. langchain_qwq talks
# to DashScope over httpx, so without this every single LLM call prints a
# "HTTP Request: POST .../chat/completions 200 OK" line — the exact noise that
# buries the actual debate narrative in the worker logs. Pin them to WARNING.
_NOISY_LOGGERS = ("httpx", "httpcore", "urllib3", "openai", "asyncio")


class _InterceptHandler(logging.Handler):
    """Route stdlib `logging` records into loguru so the whole process (celery,
    langchain, httpx, our own loguru calls) shares one sink and one format."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Walk back to the caller so file:line points at the real source.
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    """Configure loguru as the single logging sink for the process.

    Called once at API startup and once per Celery worker process (via the
    worker_process_init signal) — the worker previously never called this, so
    its logs were raw stdlib output with no debate context.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<level>{level:<7}</level>: <green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <cyan>{extra[outreach]}</cyan> - {message}"
        ),
        level=get_settings().LOG_LEVEL,
    )
    # Default the bound `outreach` field so lines without a debate context still
    # render (loguru raises on a missing {extra[...]} key otherwise).
    logger.configure(extra={"outreach": "-"})

    # Funnel stdlib logging through loguru, then quiet the noisy HTTP loggers.
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


__all__ = ["logger", "configure_logging"]
