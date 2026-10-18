"""Periodic stock data sync worker."""
import asyncio
from app.db.session import engine
from app.services.screener.ingestion import STARTER_SYMBOLS, sync_symbol as refresh_symbol
from app.workers.celery_worker import celery_app


async def refresh(symbols):
    results = []
    engine.echo = False
    try:
        for symbol in symbols:
            try:
                results.append(await refresh_symbol(symbol))
            except Exception as error:
                results.append({"symbol": symbol, "status": "failed", "error_type": type(error).__name__})
    finally:
        await engine.dispose()
    return results


@celery_app.task(name="workers.stock_sync.sync_symbol")
def sync_symbol(symbol: str) -> dict:
    return asyncio.run(refresh([symbol]))[0]


@celery_app.task(name="workers.stock_sync.sync_all")
def sync_all() -> dict:
    results = asyncio.run(refresh(STARTER_SYMBOLS))
    return {"status": "done", "count": sum(item["status"] == "synced" for item in results), "results": results}
