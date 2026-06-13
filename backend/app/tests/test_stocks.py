"""Tests for /api/v1/stocks endpoints."""
from fastapi.testclient import TestClient

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


def test_get_non_indian_symbol_returns_400() -> None:
    response = client.get("/api/v1/stocks/AAPL")

    assert response.status_code == 400


def test_search_filters_to_nse_and_bse(monkeypatch) -> None:
    async def fake_json(url: str, params: dict | None = None) -> dict:
        return {
            "quotes": [
                {"symbol": "TEST.NS", "longname": "Test NSE Ltd."},
                {"symbol": "TEST.BO", "longname": "Test BSE Ltd."},
                {"symbol": "AAPL", "longname": "Apple Inc."},
            ]
        }

    monkeypatch.setattr(stock_api, "_get_json", fake_json)

    response = client.get("/api/v1/stocks?q=test")

    assert response.status_code == 200
    symbols = [item["symbol"] for item in response.json()["items"]]
    assert symbols == ["TEST.NS", "TEST.BO"]


def test_get_quarters_has_columns_and_rows(monkeypatch) -> None:
    async def fake_summary(symbol: str, modules: list[str]) -> dict:
        return {
            "incomeStatementHistoryQuarterly": {
                "incomeStatementHistory": [
                    {
                        "endDate": {"raw": 1767139200},
                        "totalRevenue": {"raw": 10_000_000_000},
                        "netIncome": {"raw": 2_000_000_000},
                    }
                ]
            }
        }

    monkeypatch.setattr(stock_api, "_summary", fake_summary)

    response = client.get("/api/v1/stocks/TEST.NS/quarters")

    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["Dec 2025"]
    assert body["rows"][0]["label"] == "Revenue"
