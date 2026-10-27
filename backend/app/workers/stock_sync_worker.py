"""Periodic stock data sync worker."""
import asyncio
import argparse
import json
from datetime import UTC, datetime
from uuid import uuid4
from sqlalchemy import func, or_, text, update
from sqlalchemy.dialects.postgresql import insert
from app.db.session import engine
from app.models.quarterly_poll_state import QuarterlyPollState
from app.services.screener.ingestion import sync_symbol as refresh_symbol
from app.services.screener.universe import refresh_batch
from app.services.screener.indexes import sync_sp500
from app.services.filings.catalog import sync_catalog
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
    return asyncio.run(poll_once())


async def poll_once(market=None):
    """One bounded batch. The lease prevents concurrent CLI/Celery workers."""
    engine.echo = False
    owner, acquired = str(uuid4()), False
    outcome = {"started_at": datetime.now(UTC).isoformat(), "results": []}
    try:
        async with engine.begin() as connection:
            claim = {"name": "screener", "payload": {"status": "running"}, "lease_owner": owner,
                     "lease_until": func.now() + text("INTERVAL '14 minutes'")}
            statement = insert(QuarterlyPollState).values(**claim).on_conflict_do_update(
                index_elements=[QuarterlyPollState.name], set_={key: value for key, value in claim.items() if key != "name"},
                where=or_(QuarterlyPollState.lease_until.is_(None), QuarterlyPollState.lease_until <= func.now()),
            ).returning(QuarterlyPollState.name)
            acquired = (await connection.execute(statement)).scalar_one_or_none() is not None
        if not acquired:
            return {**outcome, "status": "already_running"}
        async with asyncio.timeout(13 * 60):
            outcome["catalog"] = await sync_catalog()
            try:
                outcome["sp500"] = await sync_sp500()
            except Exception as error:
                outcome["sp500"] = {"status": "unavailable", "error_type": type(error).__name__}
            outcome["results"] = await refresh_batch(market=market)
            outcome["status"] = "ok"
    except TimeoutError:
        outcome["status"] = "timeout"
    except Exception as error:
        outcome.update(status="error", error_type=type(error).__name__)
    finally:
        if acquired:
            async with engine.begin() as connection:
                await connection.execute(update(QuarterlyPollState).where(
                    QuarterlyPollState.name == "screener", QuarterlyPollState.lease_owner == owner,
                ).values(payload={**outcome, "finished_at": datetime.now(UTC).isoformat()}, lease_owner=None, lease_until=None))
        await engine.dispose()
    return outcome


async def run(*, once=False, market=None):
    while True:
        outcome = await poll_once(market)
        print(json.dumps(outcome), flush=True)
        if once:
            return int(outcome["status"] not in ("ok", "already_running"))
        results = outcome["results"]
        limited = any(item.get("error_type") == "YFRateLimitError" for item in results)
        # Each listing has its own durable due date; failures cannot starve later symbols.
        await asyncio.sleep(900 if limited or outcome["status"] != "ok" or not results else 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Continuously refresh screening financials across NSE, BSE, NYSE and NASDAQ.")
    parser.add_argument("--once", action="store_true", help="Process one resumable batch, suitable for cron")
    parser.add_argument("--market", choices=["IN", "US"])
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(run(once=args.once, market=args.market)))
    except KeyboardInterrupt:
        pass
