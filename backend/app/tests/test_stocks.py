"""Tests for /api/v1/stocks endpoints."""
from fastapi.testclient import TestClient
from types import SimpleNamespace
import pandas as pd

from app.api.v1 import stocks as stock_api
from app.main import app

client = TestClient(app)


def test_get_stock_returns_indian_live_quote_shape(monkeypatch) -> None:
    async def fake_quote(symbol: str) -> dict:
        return {
            "symbol": symbol,
            "name": "Test Listed Company",
            "price": 123.45,
            "exchange": "NSE",
            "currency": "INR",
            "currencySymbol": "INR",
        }

    monkeypatch.setattr(stock_api, "_quote", fake_quote)

    response = client.get("/api/v1/stocks/TEST.NS")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "TEST.NS"
    assert body["currency"] == "INR"


def test_get_us_symbol_returns_quote(monkeypatch) -> None:
    async def fake_json(url, params):
        return {"chart": {"result": [{"meta": {"exchangeName": "NMS", "currency": "USD", "regularMarketPrice": 200, "previousClose": 198, "exchangeTimezoneName": "America/New_York"}}]}}
    monkeypatch.setattr(stock_api, "_get_json", fake_json)
    response = client.get("/api/v1/stocks/AAPL")
    assert response.status_code == 200
    assert response.json()["exchange"] == "NASDAQ"
    assert response.json()["currency"] == "USD"
    assert response.json()["timeZone"] == "America/New_York"


def test_search_includes_indian_and_us_equities(monkeypatch) -> None:
    async def fake_json(url: str, params: dict | None = None) -> dict:
        return {
            "quotes": [
                {"symbol": "TEST.NS", "longname": "Test NSE Ltd."},
                {"symbol": "TEST.BO", "longname": "Test BSE Ltd."},
                {"symbol": "AAPL", "longname": "Apple Inc.", "exchange": "NMS", "quoteType": "EQUITY"},
                {"symbol": "BRK-B", "exchange": "NYQ", "quoteType": "EQUITY"},
                {"symbol": "AAPL", "exchange": "NMS", "quoteType": "EQUITY"},
                {"symbol": "VOD.L", "exchange": "LSE", "quoteType": "EQUITY"},
                {"symbol": "SPY", "exchange": "PCX", "quoteType": "ETF"},
                {"symbol": "BTC-USD", "exchange": "CCC", "quoteType": "CRYPTOCURRENCY"},
            ]
        }

    monkeypatch.setattr(stock_api, "_get_json", fake_json)

    response = client.get("/api/v1/stocks?q=test")

    assert response.status_code == 200
    symbols = [item["symbol"] for item in response.json()["items"]]
    assert symbols == ["TEST.NS", "TEST.BO", "AAPL", "BRK-B"]
    assert response.json()["items"][2]["currency"] == "USD"
    assert response.json()["items"][3]["baseSymbol"] == "BRK-B"


def test_get_quarters_has_columns_and_rows(monkeypatch) -> None:
    frame = pd.DataFrame({pd.Timestamp("2025-12-31"): {"Total Revenue": 10_000_000_000, "Net Income": 2_000_000_000}})
    monkeypatch.setattr(stock_api, "_fetch_yfinance_ticker", lambda symbol: SimpleNamespace(quarterly_income_stmt=frame))

    response = client.get("/api/v1/stocks/TEST.NS/quarters")

    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["Dec 2025"]
    assert body["rows"][0]["label"] == "Revenue"
    assert body["chart"][0]["totalIncome"] == 100_000
