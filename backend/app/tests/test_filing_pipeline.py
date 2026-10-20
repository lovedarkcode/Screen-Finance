"""Deterministic provider, persistence, summary, scheduling and API boundaries."""
import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.screener import screening_db
from app.config import Settings, settings
from app.db.base import Base
from app.dependencies import require_user
from app.main import app
from app.models.company import Company
from app.models.quarterly_result import QuarterlyResult
from app.models.quarterly_poll_state import QuarterlyPollState
from app.models.result_listing import ResultListing
from app.services.filings.yahoo import PROVIDER
from app.schemas.quarterly_filing import IncomeStatement
from app.services.filings import comparisons, fmp, pipeline, summary
from app.workers import quarterly_results_worker as worker


def raw(**changes):
    return {"symbol": "TEST", "fiscalYear": "2026", "period": "Q2", "date": "2026-06-30", "filingDate": "2026-07-25",
            "reportedCurrency": "USD", "revenue": 200, "netIncome": 20, "operatingIncome": 40, "eps": 1.2, "epsDiluted": 1.1, **changes}


class AsyncFixtureSession:
    def __init__(self, engine):
        self.session = Session(engine, expire_on_commit=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.session.close()

    def get_bind(self):
        return self.session.get_bind()

    async def execute(self, statement):
        return self.session.execute(statement)

    async def get(self, model, identity):
        return self.session.get(model, identity)

    async def commit(self):
        self.session.commit()


@pytest.fixture
def database():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine, tables=[Company.__table__, QuarterlyResult.__table__, QuarterlyPollState.__table__, ResultListing.__table__])
    with Session(engine) as session:
        session.add(Company(ticker="TEST", name="Test Company", sector="Technology", country="US", exchange="NASDAQ"))
        session.commit()
    yield SimpleNamespace(engine=engine, factory=lambda: AsyncFixtureSession(engine))
    engine.dispose()


class Provider:
    def __init__(self, records=None):
        self.records = records or [raw()]

    async def income_statements(self, symbol):
        return [(IncomeStatement.model_validate(row), row) for row in self.records], 0

    async def profile(self, symbol):
        return fmp.CompanyProfile.model_validate({"symbol": symbol, "companyName": "New Company", "exchange": "NSE", "country": "IN"})


async def insert_records(database, records=None):
    return await pipeline.ingest_tickers(Provider(records), ["TEST"], database.factory)


def get_rows(database):
    with Session(database.engine) as session:
        return session.scalars(select(QuarterlyResult).order_by(QuarterlyResult.period_end.desc())).all()


async def grounded_summary(company, record, history):
    allowed, _ = comparisons.findings(record, history)
    return summary.render_selection(json.dumps({"positive_triggers": [], "red_flags": [], "executive_summary": ["S_METRICS", "S_MARGIN_EPS"]}), allowed)


def test_schema_rejects_bad_figures_dates_and_annual_reports():
    for changes in ({"revenue": True}, {"revenue": "NaN"}, {"netIncome": "Infinity"}, {"period": "FY"}, {"date": "2099-01-01"}, {"filingDate": "2025-01-01"}, {"reportedCurrency": "INVALID"}):
        with pytest.raises(ValidationError):
            IncomeStatement.model_validate(raw(**changes))
    values = IncomeStatement.model_validate(raw(epsDiluted=None)).financial_values()
    assert values["eps"] == Decimal("1.2") and values["eps_basis"] == "basic"
    assert values["operating_margin"] == 20
    assert IncomeStatement.model_validate(raw(filingDate="")).filing_date is None


def test_configuration_accepts_existing_key_alias_and_website_without_exposing_keys(monkeypatch):
    monkeypatch.setenv("FMP", "isolated-fmp-secret")
    config = Settings(_env_file=None, NEBIUS_BASE_URL="https://nebius.ai", DEBUG=False)
    assert config.FMP_API_KEY.get_secret_value() == "isolated-fmp-secret"
    assert config.NEBIUS_BASE_URL == "https://api.tokenfactory.us-central1.nebius.com/v1/"
    assert "isolated-fmp-secret" not in repr(config)


@pytest.mark.parametrize("status", [401, 402, 403])
def test_fmp_rejects_entitlement_and_auth_failures_without_leaking_keys(monkeypatch, status):
    monkeypatch.setattr(settings, "FMP_API_KEY", SecretStr("isolated-fmp-key"))
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.params["apikey"] == "isolated-fmp-key"
        assert request.url.params["period"] == "quarter"
        return httpx.Response(status, text="private upstream isolated-fmp-key")
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(fmp.PipelineError) as error:
                await fmp.FMPClient(client).income_statements("TEST")
            assert str(error.value) == f"fmp_http_{status}" and not error.value.retryable
            if status == 402:
                assert error.value.http_status == 402 and error.value.reason == "PROVIDER_TIER_RESTRICTION"
    asyncio.run(run())
    assert len(calls) == 1


def test_fmp_retries_transient_errors_and_rejects_cross_listing_rows(monkeypatch):
    monkeypatch.setattr(settings, "FMP_API_KEY", SecretStr("isolated-fmp-key"))
    calls = []
    async def no_wait(*args):
        pass
    monkeypatch.setattr(fmp.asyncio, "sleep", no_wait)
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "1"}) if len(calls) == 1 else httpx.Response(200, json=[raw(), raw(symbol="OTHER")])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            records, rejected = await fmp.FMPClient(client).income_statements("TEST")
            assert len(records) == rejected == 1
    asyncio.run(run())
    assert len(calls) == 2


def test_402_is_reported_without_inserts_and_other_tickers_continue(database, caplog):
    class TierRestricted(Provider):
        async def income_statements(self, symbol):
            if symbol == "BLOCKED.NS":
                raise fmp.PipelineError("fmp_http_402", http_status=402, reason="PROVIDER_TIER_RESTRICTION")
            return await super().income_statements(symbol)
    result = asyncio.run(pipeline.ingest_tickers(TierRestricted(), ["BLOCKED.NS", "TEST"], database.factory))
    assert result[0] == {"ticker": "BLOCKED.NS", "error": "fmp_http_402", "status": "FAILED", "reason": "PROVIDER_TIER_RESTRICTION", "code": 402}
    assert result[1]["inserted"] == 1
    with Session(database.engine) as session:
        assert session.scalar(select(func.count()).select_from(Company)) == 1
        assert session.scalar(select(func.count()).select_from(QuarterlyResult)) == 1
    assert "Infrastructure limitation: HTTP 402" in caplog.text
    assert get_rows(database)[0].ai_summary is None


def test_manual_ingestion_trigger_is_protected_and_schedules_the_real_worker(monkeypatch):
    from app.api.v1 import ingestion
    from app.dependencies import require_admin
    calls = []
    async def worker(**kwargs):
        calls.append(kwargs)
        return {"status": "partial_failure"}
    monkeypatch.setattr(ingestion, "poll_once", worker)
    client = TestClient(app)
    assert client.post("/api/v1/trigger-ingestion").status_code == 401
    app.dependency_overrides[require_admin] = lambda: object()
    try:
        response = client.post("/api/v1/trigger-ingestion")
        assert response.status_code == 202 and response.json()["status"] == "SCHEDULED"
        assert calls == [{"dispose_engine": False}]
    finally:
        app.dependency_overrides.pop(require_admin, None)


def test_persistence_is_idempotent_and_ai_sees_committed_financials(database):
    async def run():
        assert (await insert_records(database))[0]["inserted"] == 1
        assert (await insert_records(database))[0]["unchanged"] == 1
        assert (await insert_records(database, [raw(revenue="200.000")]))[0]["unchanged"] == 1
        async def generate(company, record, history):
            with Session(database.engine) as session:
                assert session.scalar(select(func.count()).select_from(QuarterlyResult)) == 1
            return await grounded_summary(company, record, history)
        assert (await pipeline.summarize_pending(database.factory, generate=generate))["completed"] == 1
        assert (await pipeline.summarize_pending(database.factory, generate=generate))["completed"] == 0
    asyncio.run(run())
    rows = get_rows(database)
    assert len(rows) == 1 and rows[0].summary_status == "completed"
    assert "Executive summary" in rows[0].ai_summary and Decimal(str(rows[0].raw_json_dump["revenue"])) == 200


def test_restatement_resets_own_and_dependent_summaries(database):
    async def run():
        await insert_records(database, [raw(fiscalYear="2025", date="2025-06-30", filingDate="2025-07-20", revenue=100), raw()])
        await pipeline.summarize_pending(database.factory, generate=grounded_summary)
        assert all(row.summary_status == "completed" for row in get_rows(database))
        changed = raw(fiscalYear="2025", date="2025-06-30", filingDate="2025-07-20", revenue=90)
        outcome = await insert_records(database, [changed])
        assert outcome[0]["revised"] == 1
    asyncio.run(run())
    rows = get_rows(database)
    assert len(rows) == 2 and all(row.summary_status == "pending" and row.ai_summary is None for row in rows)
    assert rows[1].revision == 2 and rows[1].revenue == 90


def test_failed_summary_is_durable_and_retryable_and_abandoned_lease_recovers(database):
    async def unavailable(*args):
        raise fmp.PipelineError("nebius_http_503", retryable=True)
    async def run():
        await insert_records(database)
        assert (await pipeline.summarize_pending(database.factory, generate=unavailable))["failed"] == 1
        row = get_rows(database)[0]
        assert row.net_income == 20 and row.next_retry_at is not None and row.ai_summary is None
        assert (await pipeline.summarize_pending(database.factory, generate=grounded_summary))["completed"] == 0
        with Session(database.engine) as session:
            session.execute(update(QuarterlyResult).values(summary_status="processing", summary_lease_until=datetime.now(UTC) - timedelta(minutes=1)))
            session.commit()
        assert (await pipeline.summarize_pending(database.factory, generate=grounded_summary))["completed"] == 1
    asyncio.run(run())


def test_stale_summary_cannot_overwrite_a_revised_filing(database):
    async def run():
        await insert_records(database)
        async def racing(company, record, history):
            await insert_records(database, [raw(revenue=300)])
            return await grounded_summary(company, record, history)
        await pipeline.summarize_pending(database.factory, generate=racing, limit=1)
    asyncio.run(run())
    row = get_rows(database)[0]
    assert row.revenue == 300 and row.ai_summary is None and row.summary_status == "pending"


def test_comparisons_reject_noncomparable_period_currency_and_eps_basis(database):
    records = [raw(), raw(fiscalYear="2025", date="2025-06-30", filingDate="2025-07-20", revenue=100, netIncome=10),
               raw(period="Q1", date="2026-03-31", filingDate="2026-04-20", revenue=150, netIncome=30)]
    asyncio.run(insert_records(database, records))
    rows = get_rows(database)
    result = comparisons.comparisons(rows[0], rows)
    assert result["metrics"]["revenue"]["yoy"]["value"] == 100
    assert result["metrics"]["net_income"]["qoq"]["value"] == Decimal("-33.33")
    allowed, _ = comparisons.findings(rows[0], rows)
    assert "R_SEQUENTIAL_DIVERGENCE" in allowed
    rows[-1].currency = "INR"
    assert comparisons.comparisons(rows[0], rows)["metrics"]["revenue"]["yoy"]["value"] is None
    rows[1].eps_basis = "basic"
    assert comparisons.comparisons(rows[0], rows)["metrics"]["eps"]["qoq"]["value"] is None


def test_summary_selection_rejects_fabricated_claims_and_requires_two_sentences(database):
    asyncio.run(insert_records(database))
    row = get_rows(database)[0]
    allowed, _ = comparisons.findings(row, [row])
    for content in ({"positive_triggers": ["invented"], "red_flags": [], "executive_summary": ["S_METRICS", "S_MARGIN_EPS"]},
                    {"positive_triggers": [], "red_flags": [], "executive_summary": ["S_METRICS", "S_METRICS"]},
                    {"positive_triggers": [], "red_flags": [], "executive_summary": ["S_METRICS"]}):
        with pytest.raises((ValueError, ValidationError)):
            summary.render_selection(json.dumps(content), allowed)


def test_nebius_uses_selected_model_and_never_falls_back_to_nvidia(database, monkeypatch):
    asyncio.run(insert_records(database))
    row = get_rows(database)[0]
    monkeypatch.setattr(settings, "NEBIUS_API_KEY", SecretStr("isolated-nebius-key"))
    monkeypatch.setattr(settings, "NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    def handler(request):
        body = json.loads(request.content)
        assert body["model"] == settings.NEBIUS_MODEL
        assert request.headers["Authorization"] == "Bearer isolated-nebius-key"
        assert "raw_numbers" in body["messages"][1]["content"] and "comparisons" in body["messages"][1]["content"]
        return httpx.Response(200, json={"id": "fixture", "object": "chat.completion", "created": 1, "model": body["model"],
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps({"positive_triggers": [], "red_flags": [], "executive_summary": ["S_METRICS", "S_MARGIN_EPS"]})}}]})
    monkeypatch.setattr(summary, "DefaultAsyncHttpxClient", lambda **kwargs: httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs))
    company = SimpleNamespace(symbol="TEST", name="Test Company")
    assert "Executive summary" in asyncio.run(summary.generate_summary(company, row, [row]))[0]
    monkeypatch.setattr(settings, "NEBIUS_API_KEY", None)
    with pytest.raises(fmp.PipelineError, match="nebius_key_missing"):
        asyncio.run(summary.generate_summary(company, row, [row]))


def test_both_api_aliases_authentication_comparisons_and_parameter_validation(database, monkeypatch):
    asyncio.run(insert_records(database, [raw(provider=PROVIDER)]))
    with Session(database.engine) as session:
        identity = session.scalar(select(Company.id).where(Company.symbol == "TEST"))
        session.add(ResultListing(company_id=identity, exchange_code="TEST", catalog_source="Nasdaq Trader", catalog_updated_at=datetime.now(UTC), status="ready"))
        session.commit()
    asyncio.run(pipeline.summarize_pending(database.factory, generate=grounded_summary))
    async def database_dependency():
        async with database.factory() as session:
            yield session
    app.dependency_overrides[screening_db] = database_dependency
    client = TestClient(app)
    try:
        assert client.get("/api/results/latest").status_code == 401
        app.dependency_overrides[require_user] = lambda: object()
        for prefix in ("/api", "/api/v1"):
            response = client.get(prefix + "/results/latest")
            assert response.status_code == 200
            item = response.json()["items"][0]["latest_result"]
            assert item["ticker"] == "TEST" and item["ai_summary"] and item["operating_margin"] == "20.0000000000"
            assert "raw_json_dump" not in item
            assert client.get(prefix + "/results/TEST").json()["total"] == 1
            default_response = client.get(prefix + "/results")
            assert default_response.status_code == 200
            assert default_response.json()["source"] == PROVIDER
            assert default_response.json()["items"][0]["ticker"] == "TEST"
        assert client.get("/api/results/MISSING").status_code == 404
        for query in ("page=0", "page_size=101", "market=UNKNOWN"):
            assert client.get("/api/results/latest?" + query).status_code == 422
    finally:
        app.dependency_overrides.pop(screening_db, None)
        app.dependency_overrides.pop(require_user, None)


def test_scheduler_interval_and_duplicate_worker_lock(monkeypatch):
    assert worker.POLL_SECONDS == 900 and worker.RUN_TIMEOUT_SECONDS < worker.LOCK_SECONDS < worker.POLL_SECONDS
    class Transaction:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
    class Connection(Transaction):
        async def execute(self, *args):
            return SimpleNamespace(scalar_one_or_none=lambda: None)
    class Engine:
        def begin(self):
            return Connection()
        async def dispose(self):
            pass
    monkeypatch.setattr(worker, "engine", Engine())
    assert asyncio.run(worker.poll_once())["status"] == "already_running"
