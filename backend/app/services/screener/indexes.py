"""Current constituent membership, separate from exchange listings and financials."""
from datetime import UTC, datetime, timedelta
import csv
import io

import httpx
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.quarterly_poll_state import QuarterlyPollState
from app.services.filings.fmp import FMPClient, PipelineError
from app.services.filings.pipeline import insert_for
from app.schemas.quarterly_filing import normalize_ticker
from app.services.screener.validator import ScreenIssue

PUBLIC_MEMBERS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"


def public_symbols(content):
    rows = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    return sorted({normalize_ticker(row["Symbol"].strip().replace(".", "-")) for row in rows})


async def sync_sp500(session_factory=SessionLocal):
    async with session_factory() as session:
        saved = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "screener_sp500"))).scalar_one_or_none()
    if saved and datetime.fromisoformat(saved["updated_at"]) > datetime.now(UTC) - timedelta(days=1):
        return {"status": "ok", "members": len(saved["symbols"])}
    async with httpx.AsyncClient() as client:
        try:
            rows = await FMPClient(client).get("sp500-constituent", "SP500")
            symbols = sorted({normalize_ticker(row["symbol"].replace(".", "-")) for row in rows})
            source = "Financial Modeling Prep"
        except PipelineError:
            response = await client.get(PUBLIC_MEMBERS_URL, timeout=30, follow_redirects=True, headers={"User-Agent": "AssetHunter/1.0 (stock index membership refresh)"})
            response.raise_for_status()
            symbols, source = public_symbols(response.text), "DataHub S&P 500 constituents (Wikipedia-derived)"
    if not 450 <= len(symbols) <= 550:
        raise ValueError("Incomplete S&P 500 constituent response")
    payload = {"symbols": symbols, "updated_at": datetime.now(UTC).isoformat(), "source": source}
    async with session_factory() as session:
        statement = insert_for(session, QuarterlyPollState).values(name="screener_sp500", payload=payload)
        await session.execute(statement.on_conflict_do_update(index_elements=[QuarterlyPollState.name], set_={"payload": payload}))
        await session.commit()
    return {"status": "ok", "members": len(symbols)}


async def members(session):
    saved = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "screener_sp500"))).scalar_one_or_none()
    if not saved or datetime.fromisoformat(saved["updated_at"]) < datetime.now(UTC) - timedelta(days=7):
        raise ScreenIssue("Current S&P 500 membership is unavailable. Try a US-market or NYSE screen while index membership is refreshed.", "unsupported")
    return saved["symbols"]
