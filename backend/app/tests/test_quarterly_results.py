"""Quarterly results integrity and API checks with explicit synthetic data."""
import asyncio
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.screener import screening_db
from app.db.base import Base
from app.dependencies import require_user
from app.main import app
from app.models.financials import Financials
from app.models.stock import Stock
from app.services import quarterly_results as results
from app.services.screener.ingestion import normalize_rows
from app.tests.test_financial_evidence import full_snapshot
from app.tests.test_stock_analysis import NOW, QUOTE


class AsyncSessionFixture:
    def __init__(self, session):
        self.session = session

    async def execute(self, statement):
        return self.session.execute(statement)


def add_quarter(session, stock, end, sales, profit, currency="INR", **extras):
    provenance = {}
    for field, source in [("revenue", "Total Revenue"), ("net_income", "Net Income")]:
        provenance[field] = {"currency": currency, "period_end": end, "source_record": source, "validation_status": "provider"}
    provenance["result_metrics"] = {key: {"value": value, "currency": currency, "period_end": end, "source_record": "Diluted EPS" if key == "eps" else "EBITDA", "validation_status": "provider"} for key, value in extras.items()}
    record = Financials(stock_id=stock.id, period=end, period_type="quarterly", period_end=date.fromisoformat(end),
                        currency=currency, sales=sales, net_profit=profit, provenance=provenance,
                        validation_version=1, updated_at=datetime(2026, 10, 19, tzinfo=UTC))
    session.add(record)
    return record


@pytest.fixture
def dataset():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine, tables=[Stock.__table__, Financials.__table__])
    with Session(engine) as session:
        india = Stock(symbol="FIX.NS", name="Fixture India", country="IN", exchange="NSE", industry="Software", currency="INR")
        us = Stock(symbol="FIX", name="Fixture US", country="US", exchange="NASDAQ", industry="Hardware", currency="USD")
        session.add_all([india, us])
        session.flush()
        add_quarter(session, india, "2026-06-30", 200e7, 20e7, eps=2, ebitda=30e7)
        add_quarter(session, india, "2026-03-31", 160e7, -5e7, eps=1, ebitda=20e7)
        add_quarter(session, india, "2025-06-30", 100e7, 10e7, eps=1, ebitda=15e7)
        add_quarter(session, us, "2026-07-31", 300e6, 30e6, currency="USD")
        session.commit()
        yield AsyncSessionFixture(session), india, us
    engine.dispose()


def listing(dataset, **kwargs):
    return asyncio.run(results.list_results(dataset[0], **kwargs))


def test_growth_uses_comparable_quarters_and_preserves_reporting_dates(dataset):
    response = listing(dataset)
    item = response["items"][0]
    assert item["quarter_end"] == "2026-06-30" and item["announcement_date"] is None
    assert item["metrics"]["sales"]["yoy"]["value"] == 100
    assert item["metrics"]["sales"]["qoq"]["value"] == 25
    assert item["metrics"]["eps"]["value"] == 2
    assert item["metrics"]["net_profit"]["qoq"]["value"] is None
    assert "negative" in item["metrics"]["net_profit"]["qoq"]["reason"]
    assert item["previous_year_end"] == "2025-06-30"
    assert response["growing_sales"] == response["growing_profit"] == 1
    assert response["industries"] == ["Software"]
    assert item["source_url"] == "https://finance.yahoo.com/quote/FIX.NS/financials/"


def test_market_industry_quarter_search_sort_and_pagination(dataset):
    assert listing(dataset, market="US")["items"][0]["symbol"] == "FIX"
    assert listing(dataset, industry="Hardware")["items"] == []
    old = listing(dataset, quarter=date(2025, 6, 30), industry="Software")["items"][0]
    assert old["quarter_end"] == "2025-06-30" and len(old["history"]) == 1
    assert listing(dataset, q="missing")["total"] == 0
    assert listing(dataset, q="fixture india")["total"] == 1
    assert listing(dataset, market="ALL", page_size=1)["items"][0]["symbol"] == "FIX"
    assert listing(dataset, market="ALL", page_size=1, page=2)["items"][0]["symbol"] == "FIX.NS"
    assert listing(dataset, market="ALL", sort="sales_growth")["items"][0]["symbol"] == "FIX.NS"
    assert listing(dataset, market="ALL", page=20)["total"] == 2


def test_currency_eps_basis_missing_and_unverified_values_are_not_growth(dataset):
    session, india, _ = dataset
    rows = session.session.query(Financials).filter(Financials.stock_id == india.id).order_by(Financials.period_end.desc()).all()
    rows[-1].currency = "USD"
    rows[1].provenance = {**rows[1].provenance, "result_metrics": {"eps": {"value": 1, "currency": "INR", "period_end": "2026-03-31", "source_record": "Basic EPS", "validation_status": "provider"}}}
    rows[0].sales = None
    session.session.commit()
    item = listing(dataset)["items"][0]
    assert item["metrics"]["sales"]["value"] is None
    assert item["metrics"]["net_profit"]["yoy"]["value"] is None
    assert item["metrics"]["eps"]["qoq"]["value"] is None
    assert "basis differs" in item["metrics"]["eps"]["qoq"]["reason"]
    rows[0].validation_version = None
    session.session.commit()
    assert listing(dataset)["items"][0]["quarter_end"] == "2026-03-31"


def test_future_annual_and_wrong_interval_cannot_be_latest_or_comparisons(dataset):
    session, india, _ = dataset
    future = add_quarter(session.session, india, "2030-01-01", 999, 999)
    annual = add_quarter(session.session, india, "2026-09-30", 999, 999)
    annual.period_type = "annual"
    wrong = add_quarter(session.session, india, "2026-01-31", 1, 1)
    session.session.query(Financials).filter(Financials.period_end == date(2026, 3, 31)).delete()
    session.session.commit()
    item = listing(dataset)["items"][0]
    assert item["quarter_end"] == "2026-06-30" and item["previous_quarter_end"] is None
    assert item["metrics"]["sales"]["qoq"]["value"] is None
    assert future.period_end.isoformat() not in listing(dataset)["quarters"]


def test_import_retains_checked_ebitda_and_prefers_diluted_eps():
    snapshot = full_snapshot()
    frame = snapshot["frames"]["quarterly"]
    for field, value in [("EBITDA", 12), ("Diluted EPS", 1.2), ("Basic EPS", 1.5)]:
        frame.loc[field] = value
    records = normalize_rows(QUOTE, snapshot, NOW)
    latest = next(row for row in records if row["snapshot_key"] == "quarterly:2026-06-30")
    metrics = latest["provenance"]["result_metrics"]
    assert metrics["eps"]["value"] == 1.2 and metrics["eps"]["source_record"] == "Diluted EPS"
    assert metrics["ebitda"]["value"] == 12
    frame.loc["Diluted EPS"] = float("nan")
    records = normalize_rows(QUOTE, snapshot, NOW)
    latest = next(row for row in records if row["snapshot_key"] == "quarterly:2026-06-30")
    assert latest["provenance"]["result_metrics"]["eps"]["source_record"] == "Basic EPS"


def test_api_requires_authentication_and_validates_parameters(dataset):
    client = TestClient(app)
    async def database():
        yield dataset[0]
    app.dependency_overrides[screening_db] = database
    try:
        assert client.get("/api/v1/results/imported").status_code == 401
        app.dependency_overrides[require_user] = lambda: object()
        response = client.get("/api/v1/results/imported?quarter=2026-06-30&industry=Software")
        assert response.status_code == 200 and response.json()["total"] == 1
        for query in ("market=invalid", "page=0", "page_size=51", "quarter=invalid", "sort=invalid"):
            assert client.get("/api/v1/results/imported?" + query).status_code == 422
    finally:
        app.dependency_overrides.pop(screening_db, None)
        app.dependency_overrides.pop(require_user, None)
