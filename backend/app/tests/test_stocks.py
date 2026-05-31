"""Tests for /api/v1/stocks endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_stock_returns_apple() -> None:
    r = client.get("/api/v1/stocks/AAPL")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert body["name"] == "Apple Inc."


def test_get_unknown_stock_returns_404() -> None:
    r = client.get("/api/v1/stocks/ZZZZ")
    assert r.status_code == 404


def test_get_metrics_returns_list() -> None:
    r = client.get("/api/v1/stocks/AAPL/metrics")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_quarters_has_columns_and_rows() -> None:
    r = client.get("/api/v1/stocks/AAPL/quarters")
    assert r.status_code == 200
    body = r.json()
    assert "columns" in body and "rows" in body
