"""News ingestion worker."""
from app.workers.celery_worker import celery_app


@celery_app.task(name="workers.news.fetch")
def fetch_news(symbol: str | None = None) -> dict:
    return {"symbol": symbol, "fetched": 0}
