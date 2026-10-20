"""Regressions for stock-master coverage, metric selection and fresh API reads."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from asyncpg import InvalidCatalogNameError, UndefinedColumnError, UndefinedTableError
from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.main import app
from app.api.v1 import screener as api
from app.dependencies import require_user
from app.models.stock import Stock
from app.models.financials import Financials
from app.schemas.screener import ParsedScreen, ScreenDefinition
from app.services.screener import query_builder, parser, cache
from app.services.screener.validator import validate_screen
from app.agents.screener.graph import screener_graph
from app.tests.test_nl_screener import dataset, rows, definition


def screen(**kwargs):
    return validate_screen(ScreenDefinition(**kwargs))[0]


def add_stock(dataset, **kwargs):
    stock = Stock(symbol="BARE", name="No financials", country="US", exchange="NASDAQ", **kwargs)
    dataset.session.add(stock)
    dataset.session.commit()
    return stock


def add_metric(dataset, symbol="AAA", basis="annual", end=date(2024, 12, 31), observed=datetime(2025, 2, 1, tzinfo=UTC), **values):
    stock = dataset.session.query(Stock).filter_by(symbol=symbol).one()
    metadata = {field: {"validation_status": "provider", "period_end": end.isoformat() if end else None, "period": str(end) if end else "Provider period unknown", "currency": "USD", "source": "Synthetic test"} for field, value in values.items() if value is not None}
    record = Financials(stock_id=stock.id, period=str(end), period_type=basis, period_end=end, updated_at=observed, validation_version=1, provenance=metadata, **values)
    dataset.session.add(record)
    dataset.session.commit()
    return record


def execute(dataset, draft, page=1):
    return asyncio.run(screener_graph.ainvoke({"draft": draft, "session": dataset, "page": page}))["result"]


def test_all_companies_include_no_financials_unknown_currency_and_null_cap(dataset):
    add_stock(dataset)
    found, count = rows(dataset, screen())
    assert count == len(found) == 7
    assert asyncio.run(query_builder.universe_count(dataset, None)) == 7
    assert found[-1]["symbol"] == "BARE"
    assert all(item["value"] is None for item in found[-1]["metrics"].values())
    assert rows(dataset, definition())[1] == 5


def test_master_market_cap_can_filter_without_any_financials(dataset):
    add_stock(dataset, currency="USD", market_cap=40e9)
    found, _ = rows(dataset, definition(filters=[{"field": "market_cap", "operator": "gt", "value": 35e9}]))
    assert [item["symbol"] for item in found] == ["BARE"]
    assert found[0]["metrics"]["market_cap:snapshot"]["value"] == 40e9
    assert found[0]["metrics"]["market_cap:snapshot"]["period_end"] is None
    assert rows(dataset, definition(filters=[{"field": "market_cap", "operator": "gt", "value": 35e9, "period_end": "2025-12-31"}]))[1] == 0


@pytest.mark.parametrize("exchange,country,market,canonical", [(" nsi ", "India", "IN", "NSE"), ("BOM", "IND", "IN", "BSE"), ("XNSE", "IN", "IN", "NSE"), ("NMS", "USA", "US", "NASDAQ"), (" NYQ ", "US", "US", "NYSE")])
def test_market_and_exchange_normalization(dataset, exchange, country, market, canonical):
    stock = add_stock(dataset)
    stock.exchange, stock.country = exchange, country
    dataset.session.commit()
    found, _ = rows(dataset, screen(market=market, exchange=canonical))
    result = next(item for item in found if item["symbol"] == "BARE")
    assert result["market"] == market and result["exchange"] == canonical


def test_metrics_select_their_own_latest_available_period(dataset):
    add_metric(dataset, roe=80)
    add_metric(dataset, end=date(2026, 3, 31), observed=datetime(2026, 10, 17, tzinfo=UTC), revenue_growth=45)
    draft = definition(filters=[{"field": "roe", "operator": "gt", "value": 20}, {"field": "revenue_growth", "operator": "gt", "value": 40}])
    found, count = rows(dataset, draft)
    assert count == 1 and found[0]["symbol"] == "AAA"
    assert found[0]["metrics"]["roe:annual"]["value"] == 30
    assert found[0]["metrics"]["roe:annual"]["period_end"] == "2025-12-31"
    assert found[0]["metrics"]["revenue_growth:annual"]["period_end"] == "2026-03-31"


def test_ttm_snapshot_and_quarterly_are_not_annual_substitutes(dataset):
    add_metric(dataset, basis="ttm", roe=55, end=None, observed=datetime(2026, 10, 17, tzinfo=UTC))
    add_metric(dataset, basis="quarterly", net_profit_margin=45, end=date(2026, 3, 31), observed=datetime(2026, 10, 17, tzinfo=UTC))
    found, count = rows(dataset, definition(filters=[{"field": "roe", "period": "ttm", "operator": "gt", "value": 50}, {"field": "debt_to_equity", "period": "snapshot", "operator": "lt", "value": .5}, {"field": "net_profit_margin", "period": "quarterly", "operator": "gt", "value": 40}]))
    assert count == 1 and found[0]["symbol"] == "AAA"
    assert found[0]["metrics"]["roe:ttm"]["period_end"] is None


def test_as_of_excludes_later_observations_and_preserves_actual_reporting_date(dataset):
    add_metric(dataset, roe=80)
    # A future fiscal report cannot be used, even if an observation date is corrupt.
    add_metric(dataset, end=date(2030, 12, 31), roe=999)
    found, count = rows(dataset, definition(as_of=date(2025, 3, 1), filters=[{"field": "roe", "operator": "gt", "value": 50}]))
    assert count == 1 and found[0]["symbol"] == "AAA"
    assert found[0]["metrics"]["roe:annual"]["period_end"] == "2024-12-31"
    assert found[0]["metrics"]["market_cap:snapshot"]["value"] is None and found[0]["price"] is None
    assert rows(dataset, definition(filters=[{"field": "roe", "operator": "gt", "value": 500}]))[1] == 0


def test_missing_observation_date_is_not_historical_data(dataset):
    add_metric(dataset, roe=99, observed=None)
    assert rows(dataset, definition(as_of=date(2025, 3, 1), filters=[{"field": "roe", "operator": "gt", "value": 0}]))[1] == 0


def test_exact_metric_date_not_shared_row_date(dataset):
    record = add_metric(dataset, basis="snapshot", current_ratio=2, end=date(2025, 9, 30))
    record.period_end = date(2025, 12, 31)
    dataset.session.commit()
    found, count = rows(dataset, definition(filters=[{"field": "current_ratio", "operator": "gt", "value": 1, "period_end": "2025-09-30"}]))
    assert count == 1 and found[0]["metrics"]["current_ratio:snapshot:2025-09-30"]["period_end"] == "2025-09-30"


def test_total_count_and_null_sort_survive_pagination(dataset):
    add_stock(dataset)
    draft = definition(limit=2)
    pages = [rows(dataset, draft, page) for page in (1, 2, 3)]
    assert [count for _, count in pages] == [5, 5, 5]
    symbols = [item["symbol"] for page, _ in pages for item in page]
    assert len(symbols) == len(set(symbols)) == 5 and symbols[-1] == "BARE"
    out = execute(dataset, draft, page=4)
    assert out["empty_reason"] == "page_out_of_range" and out["total_count"] == 5


@pytest.mark.parametrize("kwargs,reason", [
    ({"sector": "Nonexistent"}, "no_matches"),
    ({"filters": [{"field": "roe", "operator": "gt", "value": 999}]}, "no_matches"),
    ({"filters": [{"field": "current_ratio", "operator": "gt", "value": 0}]}, "missing_metrics"),
    ({"filters": [{"field": "roe", "operator": "gt", "value": 0, "period_end": "2000-12-31"}]}, "unavailable_period"),
])
def test_empty_result_explanations(dataset, kwargs, reason):
    result = execute(dataset, definition(**kwargs))
    assert result["status"] == "success" and result["total_count"] == 0
    assert result["empty_reason"] == reason and result["explanation"]


def test_empty_database(dataset):
    dataset.session.query(Financials).delete()
    dataset.session.query(Stock).delete()
    dataset.session.commit()
    result = execute(dataset, screen())
    assert result["total_count"] == result["universe_count"] == 0
    assert result["empty_reason"] == "empty_universe"


def test_result_updates_immediately_even_without_timestamp_changes(dataset, monkeypatch):
    async def stale_cache(*args):
        pytest.fail("Results must be read from the database; only parsing is cached")
    monkeypatch.setattr(cache, "get", stale_cache)
    draft = definition(filters=[{"field": "roe", "operator": "gt", "value": 500}])
    assert execute(dataset, draft)["total_count"] == 0
    stock = dataset.session.query(Stock).filter_by(symbol="AAA").one()
    record = dataset.session.query(Financials).filter_by(stock_id=stock.id, period_type="annual").one()
    record.roe = 600
    dataset.session.commit()
    result = execute(dataset, draft)
    assert result["total_count"] == 1 and not result["cached"]


@pytest.mark.parametrize("error", [SQLAlchemyError("private-database-details"), InvalidCatalogNameError("private-catalog"), ConnectionRefusedError("private-host"), TimeoutError("private-timeout")])
def test_database_errors_return_503_without_details(dataset, monkeypatch, error):
    class FailingSession:
        bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def execute(self, *args): raise error
    monkeypatch.setattr(api, "SessionLocal", FailingSession)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=-2)
    try:
        response = TestClient(app).post("/api/v1/screener/execute", json={"screen": {}})
        assert response.status_code == 503 and "private" not in response.text
        assert "success" not in response.text
    finally:
        app.dependency_overrides.pop(require_user, None)


@pytest.mark.parametrize("error_type", [UndefinedTableError, UndefinedColumnError])
def test_missing_schema_reports_migration_action_without_leaking_sql(monkeypatch, caplog, error_type):
    error = ProgrammingError("private SQL", {"password": "private secret"}, error_type("private provider error"))
    class FailingSession:
        bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def execute(self, *args): raise error
    monkeypatch.setattr(api, "SessionLocal", FailingSession)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=-2)
    try:
        response = TestClient(app).get("/api/v1/results?page_size=12")
        assert response.status_code == 503
        assert "alembic upgrade head" in response.json()["detail"]
        assert error_type.sqlstate in caplog.text
        assert "private" not in response.text + caplog.text
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_unfiltered_natural_language_preserves_all_markets_and_no_filters(dataset, monkeypatch):
    async def parse(query): return ParsedScreen()
    async def no_limit(*args): pass
    monkeypatch.setattr(parser, "parse_query", parse)
    monkeypatch.setattr(api, "rate_limit", no_limit)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=-3)
    app.dependency_overrides[api.screening_db] = lambda: dataset
    try:
        response = TestClient(app).post("/api/v1/screener/search", json={"query": "Show all available companies without financial filters"})
        assert response.status_code == 200 and response.json()["total_count"] == 6
        assert response.json()["parsed_filters"]["filters"] == []
        assert response.json()["parsed_filters"]["market"] is None
    finally:
        app.dependency_overrides.pop(require_user, None)
        app.dependency_overrides.pop(api.screening_db, None)


def test_diagnostic_exclusions_partition_each_stage(dataset):
    draft = definition(filters=[{"field": "roe", "operator": "gt", "value": 50}])
    trace = asyncio.run(query_builder.diagnostics(dataset, draft))
    for stage in trace:
        assert stage["before"] - stage["remaining"] == stage["excluded"]
        if stage["stage"].startswith("filter"):
            assert sum(stage[key] for key in ["missing_metric", "incompatible_period", "unverified_metric", "incompatible_currency", "invalid_domain", "failed_condition"]) == stage["excluded"]


def test_diagnostics_refuse_production_before_querying():
    root = Path(__file__).resolve().parents[3]
    response = subprocess.run([sys.executable, str(root / "scripts" / "diagnose_screener.py")], env={**os.environ, "ENVIRONMENT": "production", "DEBUG": "false"}, capture_output=True, text=True)
    assert response.returncode == 2 and "development environment" in response.stderr
    assert 'database_connected' not in response.stdout
