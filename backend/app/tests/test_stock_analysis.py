"""Financial integrity, NVIDIA boundary and authenticated agent checks; no network."""
import asyncio
import json
from datetime import UTC, datetime

import httpx
import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.v1 import ai
from app.dependencies import require_user
from app.main import app
from app.schemas.ai import StockAnalysisReport
from app.services.ai import stock_analysis_service as agent


HTTP_CLIENT = httpx.AsyncClient
QUOTE = {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "exchange": "NASDAQ", "price": 200, "date": "2026-10-16T20:00:00Z"}
NOW = datetime(2026, 10, 17, tzinfo=UTC)
SELECTION = {"summary": ["F1"], "strengths": [], "risks": [], "watchItems": []}


def snapshot():
    return {"info": {"symbol": "AAPL", "exchange": "NMS", "financialCurrency": "USD", "marketCap": 1000, "trailingPE": 20}, "warnings": [], "frames": {
        "income": pd.DataFrame({pd.Timestamp("2025-12-31"): {"Total Revenue": 200, "Net Income": 40, "Operating Income": 60}, pd.Timestamp("2024-12-31"): {"Total Revenue": 100}}),
        "balance": pd.DataFrame({pd.Timestamp("2025-12-31"): {"Total Debt": 10, "Cash And Cash Equivalents": 30, "Stockholders Equity": 50, "Current Assets": 80, "Current Liabilities": 40}}),
        "cashflow": pd.DataFrame({pd.Timestamp("2025-12-31"): {"Operating Cash Flow": 70, "Capital Expenditure": -20}}),
        "quarterly": pd.DataFrame({pd.Timestamp("2026-06-30"): {"Total Revenue": 80, "Net Income": 8}}),
    }}


def report():
    data = snapshot()
    evidence, metrics, sources, warnings, trends = agent.build_evidence(QUOTE, data, NOW)
    research = agent._validate_research(json.dumps(SELECTION), evidence)
    return StockAnalysisReport(companyId="NASDAQ:AAPL", analysisRunId="isolated-analysis-run", **{k: QUOTE[k] for k in ("symbol", "exchange", "currency")}, companyName=QUOTE["name"], financialCurrency="USD", generatedAt=NOW, quoteAsOf=QUOTE["date"], model=agent.settings.NVIDIA_MODEL, research=research, metricIds=metrics, evidence=evidence, sources=sources, warnings=warnings, quality=agent.assess_quality(evidence, trends, data, NOW), trends=trends)


def test_calculations_have_correct_values_units_periods_and_inputs():
    evidence, metrics, sources, _, _ = agent.build_evidence(QUOTE, snapshot(), NOW)
    by_label = {item.label: item for item in evidence}
    for label, value in {"Net profit margin": 20, "Operating margin": 30, "Annual revenue growth": 100, "Free cash flow": 50, "Free cash flow margin": 25, "Current ratio": 2, "Debt to equity": .2, "Net debt": -20, "Quarterly net profit margin": 10}.items():
        item = by_label[label]
        assert item.value == value
        assert item.id in metrics and item.formula and item.inputs
        assert set(item.inputs) <= {raw.id for raw in evidence}
    assert by_label["Free cash flow"].currency == "USD"
    assert by_label["Annual revenue growth"].period == "2025-12-31 vs 2024-12-31"
    assert all(source.url.startswith("https://finance.yahoo.com/quote/AAPL/") for source in sources)


def test_missing_currency_zero_denominators_and_mismatched_periods_are_not_invented():
    data = snapshot()
    data["frames"]["income"].loc["Total Revenue", pd.Timestamp("2025-12-31")] = 0
    data["frames"]["balance"].loc["Stockholders Equity", pd.Timestamp("2025-12-31")] = -1
    data["frames"]["cashflow"].columns = pd.to_datetime(["2024-12-31"])
    evidence, _, _, warnings, _ = agent.build_evidence(QUOTE, data, NOW)
    labels = {item.label for item in evidence}
    assert not {"Net profit margin", "Debt to equity", "Free cash flow margin"} & labels
    assert "Annual revenue" in labels and any("non-positive" in warning.lower() for warning in warnings)
    data["info"].pop("financialCurrency")
    assert "Annual revenue" not in {item.label for item in agent.build_evidence(QUOTE, data, NOW)[0]}
    # ADR financial reporting currency is independent of the traded currency.
    data = snapshot()
    data["info"]["financialCurrency"] = "TWD"
    evidence = {item.label: item for item in agent.build_evidence(QUOTE, data, NOW)[0]}
    assert evidence["Share price"].currency == "USD" and evidence["Annual revenue"].currency == "TWD"


def test_unverifiable_citations_and_new_numbers_are_rejected():
    evidence = report().evidence
    assert agent._validate_research(json.dumps(SELECTION), evidence).summary
    for draft in [{**SELECTION, "summary": ["F999"]}, {**SELECTION, "summary": [{"text": "Margins grew by ninety nine percent.", "evidenceIds": ["E1"]}]}, {**SELECTION, "summary": ["F1", "F1"]}, {**SELECTION, "risks": ["F1"]}]:
        with pytest.raises(ValueError):
            agent._validate_research(json.dumps(draft), evidence)


def mock_nvidia(monkeypatch, handler):
    monkeypatch.setattr(agent.settings, "NVIDIA_API_KEY", SecretStr("isolated-nvidia-key"))
    monkeypatch.setattr(agent.settings, "OPENAI_API_KEY", "must-never-be-used")
    monkeypatch.setattr(agent, "DefaultAsyncHttpxClient", lambda **kwargs: HTTP_CLIENT(transport=httpx.MockTransport(handler), **kwargs))


def stream_response(content, finish_reason="stop"):
    events = [
        {"choices": []},
        {"choices": [{"index": 0, "delta": {"reasoning_content": "Private reasoning that must never appear in the report"}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {"content": content[:len(content) // 2]}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {"content": content[len(content) // 2:]}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}]},
    ]
    return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text="".join(f"data: {json.dumps(event)}\n\n" for event in events) + "data: [DONE]\n\n")


def test_nvidia_only_exact_model_and_bounded_structured_retry(monkeypatch):
    calls = []
    def provider(request):
        body = json.loads(request.content)
        calls.append(body)
        assert str(request.url) == agent.NVIDIA_URL
        assert request.headers["Authorization"] == "Bearer isolated-nvidia-key"
        assert body["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
        assert body["chat_template_kwargs"] == {"enable_thinking": True}
        assert body["stream"] is True
        assert (body["temperature"], body["top_p"], body["max_tokens"]) == (1, .95, 16384)
        return stream_response("invalid" if len(calls) == 1 else json.dumps(SELECTION))
    mock_nvidia(monkeypatch, provider)
    assert asyncio.run(agent._nvidia_research({}, report().evidence)).summary
    assert len(calls) == 2


@pytest.mark.parametrize("upstream,expected", [(400, 503), (401, 503), (403, 503), (404, 503), (422, 503), (429, 429), (500, 502)])
def test_provider_errors_are_sanitized(monkeypatch, upstream, expected):
    mock_nvidia(monkeypatch, lambda request: httpx.Response(upstream, text="private upstream detail isolated-nvidia-key"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent._nvidia_research({}, report().evidence))
    assert exc.value.status_code == expected
    assert "private" not in exc.value.detail and "isolated-nvidia-key" not in exc.value.detail


@pytest.mark.parametrize("upstream", [502, 503, 504])
def test_transient_provider_failure_retries_same_model_once(monkeypatch, upstream):
    calls, delays = [], []
    async def sleep(delay):
        delays.append(delay)
    def provider(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(upstream, text="Service temporarily overloaded")
        return stream_response(json.dumps(SELECTION))
    mock_nvidia(monkeypatch, provider)
    monkeypatch.setattr(agent.asyncio, "sleep", sleep)
    assert asyncio.run(agent._nvidia_research({}, report().evidence)).summary
    assert len(calls) == 2 and calls[0] == calls[1] and delays == [2]


def test_persistent_overload_returns_actionable_503_without_leaking_details(monkeypatch, caplog):
    calls = []
    async def sleep(delay):
        pass
    def provider(request):
        calls.append(request)
        return httpx.Response(503, text="private provider details isolated-nvidia-key")
    mock_nvidia(monkeypatch, provider)
    monkeypatch.setattr(agent.asyncio, "sleep", sleep)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent._nvidia_research({}, report().evidence))
    assert len(calls) == 2
    assert exc.value.status_code == 503 and exc.value.headers["Retry-After"] == "30"
    assert "30 seconds" in exc.value.detail
    assert "status=503" in caplog.text and agent.settings.NVIDIA_MODEL in caplog.text
    assert "private" not in caplog.text + exc.value.detail
    assert "isolated-nvidia-key" not in caplog.text + exc.value.detail


@pytest.mark.parametrize("recovers", [True, False])
def test_http_success_with_error_event_retries_without_exposing_partial_content(monkeypatch, caplog, recovers):
    calls = []
    async def sleep(delay):
        pass
    def provider(request):
        calls.append(request)
        if recovers and len(calls) == 2:
            return stream_response(json.dumps(SELECTION))
        events = [
            {"choices": [{"index": 0, "delta": {"content": "Unverified partial output"}, "finish_reason": None}]},
            {"error": {"message": "Service temporarily overloaded isolated-nvidia-key", "code": 503}},
        ]
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text="".join(f"data: {json.dumps(event)}\n\n" for event in events))
    mock_nvidia(monkeypatch, provider)
    monkeypatch.setattr(agent.asyncio, "sleep", sleep)
    if recovers:
        draft = asyncio.run(agent._nvidia_research({}, report().evidence))
        assert draft == report().research
    else:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(agent._nvidia_research({}, report().evidence))
        assert exc.value.status_code == 503 and exc.value.headers["Retry-After"] == "30"
        assert "Unverified" not in exc.value.detail
    assert len(calls) == 2 and "NVIDIA stream failed" in caplog.text
    assert "isolated-nvidia-key" not in caplog.text and "Unverified" not in caplog.text


@pytest.mark.parametrize("finish_reason", ["length", None])
def test_invalid_output_retries_only_once_and_timeout_is_safe(monkeypatch, finish_reason):
    calls = []
    def provider(request):
        calls.append(request)
        return stream_response(json.dumps(SELECTION), finish_reason)
    mock_nvidia(monkeypatch, provider)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent._nvidia_research({}, report().evidence))
    assert exc.value.status_code == 502 and len(calls) == 2
    def timeout(request):
        raise httpx.ReadTimeout("private provider timeout", request=request)
    mock_nvidia(monkeypatch, timeout)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent._nvidia_research({}, report().evidence))
    assert exc.value.status_code == 504 and "private" not in exc.value.detail


def test_missing_nvidia_key_has_no_other_provider_fallback(monkeypatch):
    monkeypatch.setattr(agent.settings, "NVIDIA_API_KEY", None)
    monkeypatch.setattr(agent.settings, "OPENAI_API_KEY", "available-but-not-authorized")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent.analyze_stock("AAPL"))
    assert exc.value.status_code == 503


def test_indian_bare_symbol_resolves_to_nse(monkeypatch):
    async def quote(symbol):
        if symbol == "RELIANCE":
            raise HTTPException(404)
        return {**QUOTE, "symbol": symbol}
    async def search(**kwargs):
        return {"items": [{"symbol": "RELIANCE.BO", "baseSymbol": "RELIANCE"}, {"symbol": "RELIANCE.NS", "baseSymbol": "RELIANCE"}]}
    monkeypatch.setattr(agent.stocks, "get_stock", quote)
    monkeypatch.setattr(agent.stocks, "list_stocks", search)
    assert asyncio.run(agent._resolve_quote("RELIANCE"))["symbol"] == "RELIANCE.NS"


def test_concurrent_analysis_is_shared_and_cached(monkeypatch):
    agent._cache.clear()
    agent._inflight.clear()
    calls = []
    async def quote(symbol):
        return QUOTE
    async def create(quote):
        calls.append(quote)
        await asyncio.sleep(.01)
        return report()
    monkeypatch.setattr(agent, "_resolve_quote", quote)
    monkeypatch.setattr(agent, "_create_report", create)
    monkeypatch.setattr(agent.settings, "NVIDIA_API_KEY", SecretStr("isolated"))
    async def run():
        a, b = await asyncio.gather(agent.analyze_stock("AAPL"), agent.analyze_stock("AAPL"))
        c = await agent.analyze_stock("AAPL")
        assert a.symbol == b.symbol == c.symbol and c.cached and len(calls) == 1
    try:
        asyncio.run(run())
    finally:
        agent._cache.clear()
        agent._inflight.clear()


def test_authenticated_endpoint_and_legacy_summary_use_real_report(monkeypatch):
    seen = []
    async def analyze(symbol):
        seen.append(symbol)
        return report()
    monkeypatch.setattr(ai, "analyze_stock", analyze)
    app.dependency_overrides[require_user] = lambda: object()
    try:
        client = TestClient(app)
        response = client.post("/api/v1/ai/analyze", json={"symbol": "AAPL"})
        assert response.status_code == 200 and response.json()["provider"] == "NVIDIA"
        assert client.post("/api/v1/ai/analyze", json={"symbol": "AAPL", "model": "other"}).status_code == 422
        summary = client.get("/api/v1/ai/summary/AAPL").json()
        assert summary["summary"] == report().research.summary[0].text and seen == ["AAPL", "AAPL"]
    finally:
        app.dependency_overrides.pop(require_user, None)
