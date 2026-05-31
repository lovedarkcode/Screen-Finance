"""Loguru-based structured logger."""
import sys

from loguru import logger

from app.config import settings


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
        enqueue=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


configure_logging()

__all__ = ["logger", "configure_logging"]
