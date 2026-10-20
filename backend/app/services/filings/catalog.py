"""Daily, uncapped listing discovery from the exchanges' public directories."""
import csv
import io
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select, update

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.quarterly_poll_state import QuarterlyPollState
from app.models.result_listing import ResultListing
from app.schemas.quarterly_filing import normalize_ticker
from app.services.filings.pipeline import insert_for

NSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
SME_URL = "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"
BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"
NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
NYSE_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def csv_rows(content, delimiter=","):
    return [{key.strip().replace(" ", "_"): (value or "").strip() for key, value in row.items() if key}
            for row in csv.DictReader(io.StringIO(content.lstrip("\ufeff")), delimiter=delimiter)]


def listing(symbol, name, exchange, code, isin=None):
    return {"symbol": normalize_ticker(symbol), "name": name.strip()[:255], "exchange": exchange,
            "country": "IN" if exchange in ("NSE", "BSE") else "US", "exchange_code": code,
            "isin": isin or None, "catalog_source": "Nasdaq Trader" if exchange in ("NYSE", "NASDAQ") else exchange}


def parse_nse(content):
    return [listing(row["SYMBOL"] + ".NS", row["NAME_OF_COMPANY"], "NSE", row["SYMBOL"], row.get("ISIN_NUMBER"))
            for row in csv_rows(content) if row.get("SYMBOL") and row.get("NAME_OF_COMPANY")]


def parse_bse(rows):
    # Yahoo uses BSE security IDs (RELIANCE.BO), not BSE numeric scrip codes.
    return [listing(row["scrip_id"] + ".BO", row.get("Issuer_Name") or row["Scrip_Name"], "BSE", str(row["SCRIP_CD"]), row.get("ISIN_NUMBER"))
            for row in rows if row.get("Status") == "Active" and row.get("Segment") == "Equity" and row.get("scrip_id")
            and not str(row.get("ISIN_NUMBER") or "").startswith("INF")]


def parse_us(content, exchange):
    rows = csv_rows(content, "|")
    return [listing((row.get("Symbol") or row["ACT_Symbol"]).replace(".", "-").replace("$", "-P"), row["Security_Name"], exchange,
                    row.get("Symbol") or row["ACT_Symbol"])
            for row in rows if row.get("Security_Name") and row.get("Test_Issue") == "N" and row.get("ETF") == "N"
            and (exchange == "NASDAQ" or row.get("Exchange") == "N")]


async def fetch_catalog(client, exchange):
    async def get(url, **kwargs):
        response = await client.get(url, timeout=45, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com/"}, **kwargs)
        response.raise_for_status()
        return response

    if exchange == "NSE":
        main = parse_nse((await get(NSE_URL)).text)
        sme = parse_nse((await get(SME_URL)).text)
        if len(main) < 1000 or len(sme) < 100:
            raise ValueError("Incomplete NSE directory")
        rows = main + sme
    elif exchange == "BSE":
        rows = parse_bse((await get(BSE_URL, params={"Group": "", "Scripcode": "", "industry": "", "segment": "Equity", "status": "Active"})).json())
    else:
        rows = parse_us((await get(NASDAQ_URL if exchange == "NASDAQ" else NYSE_URL)).text, exchange)
    # Reject error documents/truncated snapshots before touching existing membership.
    if len(rows) < 1000 or any(not row["name"] for row in rows):
        raise ValueError("Incomplete exchange directory")
    unique = {row["symbol"]: row for row in rows}
    if len(unique) < len(rows) * 0.99:
        raise ValueError("Ambiguous duplicate listing symbols")
    return list(unique.values())


async def persist_catalog(rows, exchange, session_factory=SessionLocal):
    now = datetime.now(UTC)
    async with session_factory() as session:
        # All membership changes for this exchange commit together; failed downloads
        # never deactivate the last successful catalog. Quotes/sector are preserved.
        await session.execute(update(ResultListing).where(ResultListing.company_id.in_(select(Company.id).where(Company.exchange == exchange))).values(active=False))
        for start in range(0, len(rows), 500):
            batch = rows[start:start + 500]
            statement = insert_for(session, Company).values([{key: row[key] for key in ("symbol", "name", "exchange", "country")} for row in batch])
            ids = (await session.execute(statement.on_conflict_do_update(index_elements=[Company.symbol],
                set_={key: getattr(statement.excluded, key) for key in ("name", "exchange", "country")}).returning(Company.id, Company.symbol))).all()
            id_map = {symbol: identity for identity, symbol in ids}
            statement = insert_for(session, ResultListing).values([
                {"company_id": id_map[row["symbol"]], "catalog_source": row["catalog_source"], "exchange_code": row["exchange_code"],
                 "isin": row["isin"], "active": True, "catalog_updated_at": now} for row in batch])
            await session.execute(statement.on_conflict_do_update(index_elements=[ResultListing.company_id],
                set_={key: getattr(statement.excluded, key) for key in ("catalog_source", "exchange_code", "isin", "active", "catalog_updated_at")}))
        await session.commit()


async def sync_catalog(*, force=False, session_factory=SessionLocal):
    async with session_factory() as session:
        previous = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "catalog"))).scalar_one_or_none() or {}
    now, output = datetime.now(UTC), {}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for exchange in ("NSE", "BSE", "NYSE", "NASDAQ"):
            last = previous.get(exchange, {})
            if not force and last.get("status") == "ok" and datetime.fromisoformat(last["updated_at"]) > now - timedelta(days=1):
                output[exchange] = last
                continue
            try:
                rows = await fetch_catalog(client, exchange)
                await persist_catalog(rows, exchange, session_factory)
                output[exchange] = {"status": "ok", "listings": len(rows), "updated_at": now.isoformat()}
            except Exception as error:
                output[exchange] = {**last, "status": "error", "error_type": type(error).__name__, "attempted_at": now.isoformat()}
    async with session_factory() as session:
        statement = insert_for(session, QuarterlyPollState).values(name="catalog", payload=output)
        await session.execute(statement.on_conflict_do_update(index_elements=[QuarterlyPollState.name], set_={"payload": output}))
        await session.commit()
    return output
