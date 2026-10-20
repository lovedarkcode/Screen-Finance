"""Bounded, fair refresh batches across the full persisted exchange catalog."""
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, or_, select, update

from app.config import settings
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.result_listing import ResultListing
from app.services.filings.pipeline import ingest_tickers
from app.services.filings.yahoo import YahooClient

UNAVAILABLE = {"yahoo_no_quarterly_data", "yahoo_reporting_currency_missing", "yahoo_fiscal_year_unknown", "yahoo_no_valid_quarters", "yahoo_identity_mismatch", "yahoo_exchange_mismatch"}


async def refresh_batch(*, session_factory=SessionLocal, provider=None):
    now = datetime.now(UTC)
    priorities = [value.strip().upper() for value in settings.RESULTS_TICKERS.split(",") if value.strip()]
    priorities += [symbol[:-3] + ".BO" for symbol in priorities if symbol.endswith(".NS")]
    async with session_factory() as session:
        eligible = select(Company.id, Company.symbol, ResultListing.status,
            func.row_number().over(partition_by=Company.exchange, order_by=(
                case((Company.symbol.in_(priorities), 0), else_=1),
                ResultListing.checked_at.asc().nullsfirst(), Company.symbol)).label("position")
        ).join(ResultListing, ResultListing.company_id == Company.id).where(ResultListing.active,
            or_(ResultListing.next_check_at.is_(None), ResultListing.next_check_at <= now)).subquery()
        tickers = (await session.execute(select(eligible.c.id, eligible.c.symbol).order_by(eligible.c.position, eligible.c.symbol).limit(settings.RESULTS_BATCH_SIZE))).all()
    results = []
    for identity, symbol in tickers:
        outcome = (await ingest_tickers(provider or YahooClient(), [symbol], session_factory))[0]
        error = outcome.get("error")
        status = "unavailable" if error in UNAVAILABLE else "error" if error else "ready"
        finished = datetime.now(UTC)
        async with session_factory() as session:
            await session.execute(update(ResultListing).where(ResultListing.company_id == identity).values(
                checked_at=finished, next_check_at=finished + timedelta(hours=168 if status == "unavailable" else 1 if error else settings.RESULTS_REFRESH_HOURS),
                status=status, error=error))
            await session.commit()
        results.append(outcome)
        if error == "yahoo_rate_limited":
            break  # Respect the provider block; the next scheduled batch retries later.
        await asyncio.sleep(settings.RESULTS_REQUEST_DELAY)
    return results


async def has_pending():
    async with SessionLocal() as session:
        return bool((await session.execute(select(ResultListing.company_id).where(ResultListing.active, ResultListing.status == "pending").limit(1))).first())
