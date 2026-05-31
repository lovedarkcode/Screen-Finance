"""Periodic stock data sync worker."""
from app.workers.celery_worker import celery_app


@celery_app.task(name="workers.stock_sync.sync_symbol")
def sync_symbol(symbol: str) -> dict:
    return {"symbol": symbol, "status": "synced"}


@celery_app.task(name="workers.stock_sync.sync_all")
def sync_all() -> dict:
    return {"status": "done", "count": 0}
