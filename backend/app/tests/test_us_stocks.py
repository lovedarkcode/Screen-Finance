"""Indian/US market and currency regressions, with no external provider calls."""
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import stocks
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("symbol,code,exchange", [("AAPL", "NMS", "NASDAQ"), ("F", "NYQ", "NYSE"), ("BRK.B", "NYQ", "NYSE"), ("BAC-PL", "NYQ", "NYSE"), ("^GSPC", "SNP", "S&P")])
def test_us_quotes_keep_symbol_currency_exchange_and_timestamp(monkeypatch, symbol, code, exchange):
    calls = []
    async def provider(url, params):
        calls.append(url)
        return {"chart": {"result": [{"meta": {"exchangeName": code, "currency": "USD", "regularMarketPrice": 110, "previousClose": 100, "regularMarketTime": 1767139200, "exchangeTimezoneName": "America/New_York"}}]}}
    monkeypatch.setattr(stocks, "_get_json", provider)
    response = client.get(f"/api/v1/stocks/{symbol}")
    assert response.status_code == 200
    body = response.json()
    assert (body["currency"], body["currencySymbol"], body["exchange"], body["market"]) == ("USD", "$", exchange, "US")
    assert body["baseSymbol"] == ("BRK-B" if symbol == "BRK.B" else symbol)
    assert body["changePercent"] == 10
    assert body["timeZone"] == "America/New_York"
    assert body["date"].startswith("2025-12-31")
    assert ".NS" not in calls[0]


def test_one_letter_search_and_bounded_limit(monkeypatch):
    async def provider(url, params):
        assert params["q"] == "F"
        return {"quotes": [{"symbol": "F", "exchange": "NYQ", "quoteType": "EQUITY"}]}
    monkeypatch.setattr(stocks, "_get_json", provider)
    assert client.get("/api/v1/stocks?q=F&limit=1").json()["items"][0]["symbol"] == "F"
    assert client.get("/api/v1/stocks?q=F&limit=0").status_code == 422
    assert client.get("/api/v1/stocks?q=F&limit=51").status_code == 422


def test_us_overview_ownership_and_financial_units(monkeypatch):
    frame = pd.DataFrame({pd.Timestamp("2026-06-30"): {"Total Revenue": 10_000_000, "Pretax Income": 2_000_000, "Net Income": 1_500_000, "Diluted EPS": 2.5, "Total Assets": 20_000_000, "Operating Cash Flow": 5_000_000}})
    info = {"currency": "USD", "financialCurrency": "USD", "marketCap": 2_000_000_000, "totalRevenue": 10_000_000, "trailingEps": 2.5, "sector": "Technology"}
    ticker = SimpleNamespace(info=info, quarterly_income_stmt=frame, income_stmt=frame, balance_sheet=frame, cashflow=frame, history=lambda **kwargs: pd.DataFrame())
    monkeypatch.setattr(stocks.yf, "Ticker", lambda symbol: ticker)
    monkeypatch.setattr(stocks, "_fetch_yfinance_ticker", lambda symbol: ticker)
    monkeypatch.setattr(stocks, "_load_shareholding", lambda symbol: [])
    overview = client.get("/api/v1/stocks/AAPL/overview")
    assert overview.status_code == 200
    metrics = {item["id"]: item for item in overview.json()["metrics"]}
    assert (metrics["marketCap"]["value"], metrics["marketCap"]["unit"], metrics["marketCap"]["currency"]) == (2_000_000_000, "compact", "USD")
    assert metrics["eps"]["unit"] == "currency"
    assert client.get("/api/v1/stocks/AAPL/shareholding").status_code == 200
    for endpoint in ["quarters", "profit-loss", "balance-sheet", "cash-flow"]:
        response = client.get(f"/api/v1/stocks/AAPL/{endpoint}")
        assert response.status_code == 200
        assert response.json()["currency"] == "USD"
        assert response.json()["unit"] == "Figures in USD Millions"
        assert "INR" not in str(response.json())
    quarters = client.get("/api/v1/stocks/AAPL/quarters").json()
    assert quarters["rows"][0]["values"] == ["USD 10 Million"]
    assert quarters["chartUnit"] == "Millions"
    assert (quarters["chart"][0]["totalIncome"], quarters["chart"][0]["eps"]) == (10, 2.5)
    # A US listing can report its accounts in another currency (e.g. an ADR).
    info["financialCurrency"] = "TWD"
    report = client.get("/api/v1/stocks/TSM/quarters").json()
    assert report["currency"] == "TWD"
    assert report["rows"][0]["values"] == ["TWD 10 Million"]
    overview = client.get("/api/v1/stocks/TSM/overview").json()
    assert overview["currency"] == "USD"
    metrics = {item["id"]: item for item in overview["metrics"]}
    assert metrics["revenue"]["currency"] == "TWD"
    assert metrics["marketCap"]["currency"] == "USD"


def test_us_peers_stay_in_us_market(monkeypatch):
    seen = []
    monkeypatch.setattr(stocks, "_fetch_yfinance_ticker", lambda symbol: SimpleNamespace(info={"sector": "Technology", "marketCap": 1e9}))
    async def provider(symbol):
        seen.append(symbol)
        return {"symbol": symbol, "currency": "USD", "exchange": "NASDAQ"}
    monkeypatch.setattr(stocks, "_quote", provider)
    response = client.get("/api/v1/stocks/AAPL/peers")
    assert response.status_code == 200
    assert len(response.json()) >= 2
    assert all(not symbol.endswith((".NS", ".BO")) for symbol in seen)
    assert all(item["currency"] == "USD" for item in response.json())


def test_indian_ampersand_symbol_is_encoded_only_for_http(monkeypatch):
    calls = []
    async def provider(url, params):
        calls.append(url)
        return {"chart": {"result": [{"meta": {"currency": "INR"}}]}}
    monkeypatch.setattr(stocks, "_get_json", provider)
    quote = client.get("/api/v1/stocks/M%26M.NS").json()
    assert quote["symbol"] == "M&M.NS"
    assert "M%26M.NS" in calls[0]
    assert stocks._normalize_symbol("M&M.NS") == "M&M.NS"


def test_invalid_or_foreign_listing_and_missing_us_quote(monkeypatch):
    for symbol in ["VOD.L", "AAPL%3Fbad", "AAPL%20MSFT"]:
        assert client.get(f"/api/v1/stocks/{symbol}").status_code == 400
    async def missing(*args, **kwargs):
        raise httpx.HTTPStatusError("Missing", request=httpx.Request("GET", "https://example.test"), response=httpx.Response(404))
    monkeypatch.setattr(stocks, "_get_json", missing)
    assert client.get("/api/v1/stocks/MISSING").status_code == 404
