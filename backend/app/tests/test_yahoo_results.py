"""Financial identity, full catalogs, latest-per-listing pagination and refresh recovery."""
import asyncio
from datetime import UTC, date, datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.screener import screening_db
from app.config import settings
from app.dependencies import require_user
from app.main import app
from app.models.company import Company
from app.models.result_listing import ResultListing
from app.services.filings import catalog, pipeline, refresh, yahoo
from app.services.filings.fmp import PipelineError
from app.tests.test_filing_pipeline import Provider, database, get_rows, raw


def test_uncapped_exchange_parsers_and_yahoo_symbol_mapping():
    header = "SYMBOL,NAME OF COMPANY, SERIES, ISIN NUMBER\n"
    rows = catalog.parse_nse(header + "\n".join(f"C{i},Company {i},EQ,INE{i:09}\n" for i in range(1200)))
    assert len(rows) == 1200 and rows[-1]["symbol"] == "C1199.NS"
    bse = [{"scrip_id": "RELIANCE", "SCRIP_CD": "500325", "Scrip_Name": "Reliance", "Status": "Active", "Segment": "Equity", "ISIN_NUMBER": "INE002A01018"}]
    assert catalog.parse_bse(bse)[0]["symbol"] == "RELIANCE.BO"
    assert not catalog.parse_bse([{**bse[0], "ISIN_NUMBER": "INF204KB17R6"}])
    us = "ACT Symbol|Security Name|Exchange|Test Issue|ETF\nBRK.B|Berkshire|N|N|N\nBAC$B|Bank preferred|N|N|N\nETF|Fund|N|N|Y\nTEST|Test|N|Y|N\nFile Creation Time: x||||\n"
    assert [row["symbol"] for row in catalog.parse_us(us, "NYSE")] == ["BRK-B", "BAC-PB"]


def test_yahoo_normalization_preserves_reported_metrics_and_fiscal_years():
    quarterly = pd.DataFrame({pd.Timestamp("2026-06-30"): {"TotalRevenue": 200, "NetIncome": 20, "OperatingIncome": 40, "DilutedEPS": 1.25}})
    annual = pd.DataFrame({pd.Timestamp("2026-03-31"): {"TotalRevenue": 700}})
    info = {"symbol": "TEST.NS", "exchange": "NSI", "financialCurrency": "INR"}
    records, rejected = yahoo.normalize_statements("TEST.NS", info, quarterly, annual)
    statement, evidence = records[0]
    assert rejected == 0 and statement.fiscal_year == 2027 and statement.quarter_period == "Q1"
    assert statement.filing_date is None and statement.provider == yahoo.PROVIDER
    assert statement.financial_values()["operating_margin"] == 20
    assert evidence["provider_fields"]["NetIncome"] == "20.0000000000"
    assert yahoo.normalize_statements("TEST.NS", {**info, "exchange": None}, quarterly, annual)[0]
    assert yahoo.fiscal_period(date(2026, 6, 27), date(2025, 9, 27)) == (2026, "Q3")
    for bad_info, expected in (({**info, "symbol": "OTHER.NS"}, "yahoo_identity_mismatch"),
                               ({**info, "exchange": "BSE"}, "yahoo_exchange_mismatch"),
                               ({**info, "financialCurrency": None}, "yahoo_reporting_currency_missing")):
        with pytest.raises(PipelineError, match=expected):
            yahoo.normalize_statements("TEST.NS", bad_info, quarterly, annual)
    with pytest.raises(PipelineError, match="yahoo_no_quarterly_data"):
        yahoo.normalize_statements("TEST.NS", info, pd.DataFrame(), annual)
    with pytest.raises(PipelineError, match="yahoo_fiscal_year_unknown"):
        yahoo.normalize_statements("TEST.NS", info, quarterly, pd.DataFrame())


def test_catalog_refresh_preserves_existing_financial_state_and_deactivates_removed_listings(database):
    async def run():
        first = catalog.listing("FIRST.NS", "First", "NSE", "FIRST", "INE123")
        second = catalog.listing("SECOND.NS", "Second", "NSE", "SECOND")
        await catalog.persist_catalog([first, second], "NSE", database.factory)
        with Session(database.engine) as session:
            row = session.scalar(select(ResultListing).join(Company).where(Company.symbol == "FIRST.NS"))
            row.status, row.checked_at = "ready", datetime.now(UTC)
            session.commit()
        await catalog.persist_catalog([{**first, "name": "Updated First"}], "NSE", database.factory)
    asyncio.run(run())
    with Session(database.engine) as session:
        rows = session.execute(select(Company, ResultListing).join(ResultListing)).all()
        assert len(rows) == 2
        assert rows[0][0].name == "Updated First" and rows[0][1].status == "ready" and rows[0][1].checked_at
        assert rows[0][1].active and not rows[1][1].active


def test_api_lists_full_catalog_and_only_latest_yahoo_period_per_listing(database):
    async def run():
        await catalog.persist_catalog([catalog.listing(f"STOCK{i}.NS", f"Stock {i}", "NSE", f"STOCK{i}") for i in range(25)], "NSE", database.factory)
        await pipeline.ingest_tickers(Provider([raw(symbol="STOCK0.NS", provider=yahoo.PROVIDER), raw(symbol="STOCK0.NS", provider=yahoo.PROVIDER, period="Q1", date="2026-03-31")]), ["STOCK0.NS"], database.factory)
        # A different provider's newer report must not leak into Yahoo responses.
        await pipeline.ingest_tickers(Provider([raw(symbol="STOCK0.NS", period="Q3", date="2026-09-30", filingDate="2026-10-15")]), ["STOCK0.NS"], database.factory)
    asyncio.run(run())
    async def dependency():
        async with database.factory() as session:
            yield session
    app.dependency_overrides[screening_db] = dependency
    app.dependency_overrides[require_user] = lambda: object()
    try:
        with TestClient(app) as client:
            first = client.get("/api/results?exchange=NSE&page_size=12").json()
            assert first["total"] == 25 and len(first["items"]) == 12
            assert first["coverage"]["listed"] == 25 and first["coverage"]["with_results"] == 1
            assert first["items"][0]["latest_result"]["quarter_period"] == "Q2"
            assert any(item["latest_result"] is None for item in first["items"])
            second = client.get("/api/results?exchange=NSE&page_size=12&page=2").json()
            assert not {row["company_id"] for row in first["items"]} & {row["company_id"] for row in second["items"]}
            assert client.get("/api/results?exchange=BSE").json()["total"] == 0
            assert client.get("/api/results?q=STOCK0.NS").json()["total"] == 1
            assert client.get("/api/results/STOCK0.NS").json()["total"] == 2
            assert client.get("/api/results?status=ready").json()["total"] == 0
            assert client.get("/api/results?exchange=INVALID").status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_refresh_batches_are_fair_durable_and_dont_repeat_checked_symbols(database, monkeypatch):
    monkeypatch.setattr(settings, "RESULTS_BATCH_SIZE", 2)
    monkeypatch.setattr(settings, "RESULTS_REQUEST_DELAY", 0)
    monkeypatch.setattr(settings, "RESULTS_TICKERS", "")
    calls = []
    class EmptyProvider:
        async def income_statements(self, symbol):
            calls.append(symbol)
            raise PipelineError("yahoo_no_quarterly_data")
    async def run():
        for exchange, suffix in (("NSE", ".NS"), ("BSE", ".BO")):
            await catalog.persist_catalog([catalog.listing(f"C{i}{suffix}", "Company", exchange, str(i)) for i in range(3)], exchange, database.factory)
        await refresh.refresh_batch(session_factory=database.factory, provider=EmptyProvider())
        assert len(calls) == 2 and any(t.endswith(".NS") for t in calls) and any(t.endswith(".BO") for t in calls)
        await refresh.refresh_batch(session_factory=database.factory, provider=EmptyProvider())
    asyncio.run(run())
    assert len(set(calls)) == 4
    with Session(database.engine) as session:
        checked = session.scalars(select(ResultListing).where(ResultListing.status == "unavailable")).all()
        assert len(checked) == 4 and all(row.next_check_at > row.checked_at for row in checked)


def test_rate_limit_stops_batch_and_leaves_remaining_tickers_pending(database, monkeypatch):
    monkeypatch.setattr(settings, "RESULTS_BATCH_SIZE", 3)
    class LimitedProvider:
        async def income_statements(self, symbol):
            raise PipelineError("yahoo_rate_limited", retryable=True)
    async def run():
        await catalog.persist_catalog([catalog.listing(f"C{i}.NS", "Company", "NSE", str(i)) for i in range(3)], "NSE", database.factory)
        result = await refresh.refresh_batch(session_factory=database.factory, provider=LimitedProvider())
        assert len(result) == 1 and result[0]["error"] == "yahoo_rate_limited"
    asyncio.run(run())
    with Session(database.engine) as session:
        rows = session.scalars(select(ResultListing)).all()
        assert sum(row.status == "pending" for row in rows) == 2
        assert sum(row.status == "error" and row.next_check_at is not None for row in rows) == 1
