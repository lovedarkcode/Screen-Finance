"""Standalone 15-minute filing worker; supports one-shot cron execution too."""
import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from time import monotonic
from uuid import uuid4

from sqlalchemy import func, or_, text, update
from sqlalchemy.dialects.postgresql import insert

from app.db.session import engine
from app.models.quarterly_poll_state import QuarterlyPollState
from app.services.filings.pipeline import retry_failed, summarize_pending
from app.services.filings.catalog import sync_catalog
from app.services.filings.refresh import has_pending, refresh_batch

logger = logging.getLogger("screen-finance.filings")
POLL_SECONDS = 15 * 60
RUN_TIMEOUT_SECONDS = 13 * 60
LOCK_SECONDS = 14 * 60


async def poll_once(*, retry=False, dispose_engine=True):
    output = {"started_at": datetime.now(UTC).isoformat(), "interval_seconds": POLL_SECONDS}
    engine.echo = False
    owner, acquired = str(uuid4()), False
    try:
        # Atomic database-time lease works through poolers and commits immediately.
        # Its 14-minute lifetime exceeds the enforced 13-minute processing budget.
        async with engine.begin() as connection:
            claim = {"name": "filings", "payload": {**output, "status": "running"}, "lease_owner": owner,
                     "lease_until": func.now() + text("INTERVAL '14 minutes'")}
            statement = insert(QuarterlyPollState).values(**claim).on_conflict_do_update(
                index_elements=[QuarterlyPollState.name], set_={key: value for key, value in claim.items() if key != "name"},
                where=or_(QuarterlyPollState.lease_until.is_(None), QuarterlyPollState.lease_until <= func.now()),
            ).returning(QuarterlyPollState.name)
            acquired = (await connection.execute(statement)).scalar_one_or_none() is not None
        if not acquired:
            return {**output, "status": "already_running"}
        async with asyncio.timeout(RUN_TIMEOUT_SECONDS):
            if retry:
                await retry_failed()
            output["provider"] = "Yahoo Finance/yfinance"
            output["catalog"] = await sync_catalog()
            output["tickers"] = await refresh_batch()
            output["summaries"] = await summarize_pending()
            output["status"] = "partial_failure" if any("error" in item for item in output["tickers"]) or output["summaries"]["failed"] else "ok"
    except TimeoutError:
        output["status"] = "timeout"
    except Exception as error:
        output.update(status="error", error="poll_failed", error_type=type(error).__name__)
    finally:
        if acquired:
            output["finished_at"] = datetime.now(UTC).isoformat()
            try:
                async with engine.begin() as connection:
                    await connection.execute(update(QuarterlyPollState).where(QuarterlyPollState.name == "filings", QuarterlyPollState.lease_owner == owner)
                                             .values(payload=output, lease_owner=None, lease_until=None))
            except Exception as error:
                logger.warning("Worker status unavailable: error_type=%s", type(error).__name__)
        if dispose_engine:
            await engine.dispose()
    output["finished_at"] = datetime.now(UTC).isoformat()
    return output


async def run(*, once=False, retry=False, bootstrap=False):
    while True:
        started = monotonic()
        outcome = await poll_once(retry=retry)
        retry = False
        print(json.dumps(outcome), flush=True)
        if once:
            return 0 if outcome["status"] in ("ok", "already_running") else 1
        # Fixed cadence without overlapping jobs or starting one loop per web worker.
        pending = bootstrap and outcome["status"] in ("ok", "partial_failure") and not any(item.get("error") == "yahoo_rate_limited" for item in outcome.get("tickers", [])) and await has_pending()
        await asyncio.sleep(5 if pending else max(1, POLL_SECONDS - (monotonic() - started)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run once, suitable for an external 15-minute cron")
    parser.add_argument("--retry-failed", action="store_true", help="Reset failed summaries after fixing credentials, quota or configuration")
    parser.add_argument("--bootstrap", action="store_true", help="Continue paced initial-discovery batches until all catalog listings have been checked, then poll every 15 minutes")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        return asyncio.run(run(once=args.once, retry=args.retry_failed, bootstrap=args.bootstrap))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
