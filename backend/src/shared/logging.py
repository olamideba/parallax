import sys

from loguru import logger

from src.config import get_settings


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<level>{level:<7}</level>: <green>{time:YYYY-MM-DD HH:mm:ss}</green> - {message}",
        level=get_settings().LOG_LEVEL,
    )


__all__ = ["logger", "configure_logging"]
