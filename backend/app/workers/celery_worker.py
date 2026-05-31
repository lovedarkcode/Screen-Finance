"""Celery application factory."""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "screen_finance",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.stock_sync_worker",
        "app.workers.news_worker",
        "app.workers.embeddings_worker",
        "app.workers.filing_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
