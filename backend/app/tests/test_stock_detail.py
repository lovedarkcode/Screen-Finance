"""Data-integrity checks for the stock detail view; no provider calls."""
from types import SimpleNamespace

import httpx
import pandas as pd
from fastapi.testclient import TestClient

from app.api.v1 import stocks
from app.main import app

client = TestClient(app)


def test_quote_uses_previous_session_and_actual_market_time(monkeypatch):
    async def provider(*args, **kwargs):
        return {"chart": {"result": [{"meta": {"regularMarketPrice": 110, "chartPreviousClose": 80, "regularMarketTime": 1767139200}, "indicators": {"quote": [{"close": [80, 90, 100, 110]}]}}]}}
    monkeypatch.setattr(stocks, "_get_json", provider)
    quote = client.get("/api/v1/stocks/TEST.NS").json()
    assert quote["change"] == 10
    assert quote["changePercent"] == 10
    assert quote["date"].startswith("2025-12-31")


def test_intraday_keeps_prices_without_volume_and_uses_minute_interval(monkeypatch):
    calls = []
    async def provider(url, params):
        calls.append(params)
        return {"chart": {"result": [{"timestamp": [1767139200, 1767139260], "indicators": {"quote": [{"close": [100, 101]}]}}]}}
    monkeypatch.setattr(stocks, "_get_json", provider)
    response = client.get("/api/v1/stocks/TEST.NS/chart?range=1D")
    assert response.status_code == 200
    assert calls[0]["interval"] == "1m"
    assert [row["price"] for row in response.json()] == [100, 101]
    assert response.json()[0]["volume"] is None
    assert response.json()[0]["date"] != response.json()[1]["date"]
    assert client.get("/api/v1/stocks/TEST.NS/chart?range=INVALID").status_code == 422


def test_missing_lookback_is_not_zero_return():
    history = pd.DataFrame({"Close": [100, 120]}, index=pd.to_datetime(["2026-10-01", "2026-10-15"], utc=True))
    returns = stocks._history_returns(history)
    assert abs(returns[0]["value"] - 20) < 1e-9
    assert returns[-1]["value"] is None


def test_ratios_preserve_zero_and_reject_nonfinite():
    metrics = {item["id"]: item["value"] for item in stocks._overview_metrics({"debtToEquity": 0, "returnOnEquity": float("nan"), "operatingMargins": 0}, None)}
    assert metrics["debtToEquity"] == 0
    assert metrics["roe"] is None
    assert metrics["operatingMargin"] == 0
    assert metrics["allTimeHigh"] is None


def test_financial_amounts_convert_to_lakhs_but_eps_does_not():
    frame = pd.DataFrame({pd.Timestamp("2026-06-30"): {"Total Revenue": 10_000_000, "Pretax Income": 2_000_000, "Net Income": 1_500_000, "Diluted EPS": 2.5}})
    row = stocks._quarterly_chart(frame)[0]
    assert (row["totalIncome"], row["profitBeforeTax"], row["netProfitLoss"], row["eps"]) == (100, 20, 15, 2.5)


def test_ownership_snapshot_is_not_a_fabricated_quarter(monkeypatch):
    holders = pd.DataFrame({"Value": {"insidersPercentHeld": 0.6, "institutionsPercentHeld": 0.25}})
    monkeypatch.setattr(stocks.yf, "Ticker", lambda symbol: SimpleNamespace(major_holders=holders))
    report = stocks._load_shareholding("TEST.NS")[0]
    assert report["periodEnd"] is None
    assert sum(item["value"] for item in report["holdings"]) == 100
    holders.loc["institutionsPercentHeld", "Value"] = 0.8
    assert stocks._load_shareholding("TEST.NS") == []


def test_provider_404_is_distinct_from_provider_failure(monkeypatch):
    async def provider(*args, **kwargs):
        raise httpx.HTTPStatusError("Missing", request=httpx.Request("GET", "https://example.test"), response=httpx.Response(404))
    monkeypatch.setattr(stocks, "_get_json", provider)
    assert client.get("/api/v1/stocks/MISSING.NS").status_code == 404
