"""Reuse exchange catalogs; refresh validated financials with a durable retry queue."""
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update

from app.config import settings
from app.db.session import SessionLocal
from app.models.result_listing import ResultListing
from app.models.stock import Stock
from app.services.screener.ingestion import sync_symbol


async def refresh_batch(*, market=None, session_factory=SessionLocal, refresh=None, delay=None):
    now = datetime.now(UTC)
    async with session_factory() as session:
        eligible = select(Stock.id, Stock.symbol, func.row_number().over(
            partition_by=Stock.exchange,
            order_by=(ResultListing.screener_checked_at.asc().nullsfirst(), Stock.symbol),
        ).label("position")).join(ResultListing, ResultListing.company_id == Stock.id).where(
            ResultListing.active,
            or_(ResultListing.screener_next_check_at.is_(None), ResultListing.screener_next_check_at <= now),
        )
        if market:
            eligible = eligible.where(Stock.country == market)
        eligible = eligible.subquery()
        tickers = (await session.execute(select(eligible.c.id, eligible.c.symbol).order_by(
            eligible.c.position, eligible.c.symbol).limit(settings.RESULTS_BATCH_SIZE))).all()
    results = []
    for identity, symbol in tickers:
        try:
            outcome = await (refresh or sync_symbol)(symbol)
            error = None
        except Exception as failure:
            status = getattr(getattr(failure, "response", None), "status_code", None) or getattr(failure, "status_code", None)
            error = "YFRateLimitError" if status == 429 else type(failure).__name__
            outcome = {"symbol": symbol, "status": "failed", "error_type": error}
        finished = datetime.now(UTC)
        async with session_factory() as session:
            await session.execute(update(ResultListing).where(ResultListing.company_id == identity).values(
                screener_checked_at=finished, screener_error=error,
                screener_next_check_at=finished + timedelta(hours=6 if error else settings.RESULTS_REFRESH_HOURS)))
            await session.commit()
        results.append(outcome)
        if error == "YFRateLimitError":
            break
        await asyncio.sleep(settings.RESULTS_REQUEST_DELAY if delay is None else delay)
    return results
