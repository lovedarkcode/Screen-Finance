"""SEC / annual report ingestion worker."""
from app.workers.celery_worker import celery_app


@celery_app.task(name="workers.filings.ingest")
def ingest_filing(url: str, symbol: str) -> dict:
    return {"url": url, "symbol": symbol, "status": "queued"}
