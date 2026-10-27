"""Regression checks for broad discovery, selected markets and index membership."""
import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1 import screener as api
from app.dependencies import require_user
from app.main import app
from app.models.result_listing import ResultListing
from app.models.quarterly_poll_state import QuarterlyPollState
from app.models.stock import Stock
from app.schemas.screener import ParsedScreen, ScreenDefinition
from app.services.filings import catalog
from app.services.screener import indexes, ingestion, parser, query_builder, universe
from app.services.screener.validator import ScreenIssue, validate_screen
from app.tests.test_filing_pipeline import database
from app.tests.test_nl_screener import dataset


def test_selected_market_controls_generic_prompts_and_rejects_conflicts(dataset, monkeypatch):
    async def parse(query, market=None):
        return ParsedScreen()  # The model may omit the selector; the server applies it.
    async def no_limit(*args): pass
    monkeypatch.setattr(parser, "parse_query", parse)
    monkeypatch.setattr(api, "rate_limit", no_limit)
    app.dependency_overrides[require_user] = lambda: object()
    app.dependency_overrides[api.screening_db] = lambda: dataset
    try:
        client = TestClient(app)
        for market, count in [("IN", 2), ("US", 4)]:
            body = client.post("/api/v1/screener/search", json={"query": "Show all companies", "market": market}).json()
            assert body["status"] == "success" and body["total_count"] == count
            assert body["parsed_filters"]["market"] == market
        body = client.post("/api/v1/screener/search", json={"query": "Show US companies", "market": "IN"}).json()
        assert body["status"] == "clarification" and not body["stocks"]
    finally:
        app.dependency_overrides.pop(require_user, None)
        app.dependency_overrides.pop(api.screening_db, None)


def test_all_matching_listings_survive_pagination(dataset):
    dataset.session.add_all([Stock(symbol=f"NEW{i:03}.NS", name=f"New company {i}", country="IN", exchange="NSE", market_cap=20e9, currency="INR") for i in range(60)])
    dataset.session.commit()
    screen, _ = validate_screen(ScreenDefinition(market="IN", limit=25, filters=[{"field": "market_cap", "operator": "gt", "value": 10e9}]))
    symbols = []
    for page in (1, 2, 3):
        statement, count, _ = query_builder.statements(screen, page)
        assert dataset.session.execute(count).scalar_one() == 62
        symbols.extend(row[0].symbol for row in dataset.session.execute(statement))
    assert len(symbols) == len(set(symbols)) == 62
    assert asyncio.run(query_builder.eligible_count(dataset, screen)) == 62


def test_financial_coverage_is_distinct_from_matches(dataset):
    screen, _ = validate_screen(ScreenDefinition(market="US", filters=[{"field": "roe", "operator": "gt", "value": 20}]))
    _, count, _ = query_builder.statements(screen, 1)
    assert dataset.session.execute(count).scalar_one() == 3
    assert asyncio.run(query_builder.eligible_count(dataset, screen)) == 4


@pytest.mark.parametrize("name", ["S&P 500", "S&P500", "SP500", "Standard and Poor's 500"])
def test_index_membership_is_verified_and_bound(dataset, name):
    screen, _ = validate_screen(ParsedScreen(market="US", index="SP500"), f"Show {name} companies")
    statement, count, _ = query_builder.statements(screen, 1, ["AAA", "BBB"])
    assert dataset.session.execute(count).scalar_one() == 2
    assert {row[0].symbol for row in dataset.session.execute(statement)} == {"AAA", "BBB"}
    with pytest.raises(ValueError, match="membership"):
        query_builder.statements(screen, 1)
    with pytest.raises(ScreenIssue, match="index membership"):
        validate_screen(ParsedScreen(market="US"), f"Show {name} companies")


def test_stale_or_missing_index_never_becomes_all_us_stocks(database):
    async def run():
        async with database.factory() as session:
            with pytest.raises(ScreenIssue, match="unavailable"):
                await indexes.members(session)
        with Session(database.engine) as session:
            session.add(QuarterlyPollState(name="screener_sp500", payload={"symbols": ["TEST"], "updated_at": (datetime.now(UTC) - timedelta(days=8)).isoformat()}))
            session.commit()
        async with database.factory() as session:
            with pytest.raises(ScreenIssue, match="unavailable"):
                await indexes.members(session)
    asyncio.run(run())


def test_public_membership_csv_normalizes_share_classes():
    assert indexes.public_symbols('Symbol,Security\nBRK.B,Berkshire\nAAPL,Apple\n') == ["AAPL", "BRK-B"]


def test_refresh_does_not_substitute_a_different_market_listing(monkeypatch):
    async def quote(symbol):
        return {"symbol": symbol + ".NS"}
    monkeypatch.setattr(ingestion, "_resolve_quote", quote)
    with pytest.raises(ValueError, match="different listing"):
        asyncio.run(ingestion.sync_symbol("TEST"))


def test_refresh_uses_full_catalog_and_durable_retries(database):
    async def run():
        await catalog.persist_catalog([catalog.listing(f"NEW{i}.NS", f"Company {i}", "NSE", f"NEW{i}") for i in range(20)], "NSE", database.factory)
        await catalog.persist_catalog([catalog.listing("USNEW", "US company", "NYSE", "USNEW")], "NYSE", database.factory)
        visited = []
        async def refresh(symbol):
            visited.append(symbol)
            if symbol == "NEW0.NS":
                raise ValueError("No provider data")
            return {"symbol": symbol, "status": "synced"}
        results = await universe.refresh_batch(market="IN", session_factory=database.factory, refresh=refresh, delay=0)
        assert len(results) == 20 and len(set(visited)) == 20 and "USNEW" not in visited
        assert len([item for item in results if item["status"] == "synced"]) == 19
        assert await universe.refresh_batch(market="IN", session_factory=database.factory, refresh=refresh, delay=0) == []
        with Session(database.engine) as session:
            rows = session.scalars(select(ResultListing).join(Stock).where(Stock.country == "IN")).all()
            assert all(row.screener_checked_at and row.screener_next_check_at for row in rows)
            assert all(row.checked_at is None for row in rows)  # Separate from quarterly refresh.
            assert sum(row.screener_error is not None for row in rows) == 1
    asyncio.run(run())
