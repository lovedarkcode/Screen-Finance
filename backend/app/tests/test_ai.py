"""Tests for /api/v1/ai endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_summary() -> None:
    r = client.get("/api/v1/ai/summary/AAPL")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert isinstance(body["keyPoints"], list)


def test_ai_chat() -> None:
    r = client.post("/api/v1/ai/chat", json={"message": "Is AAPL a buy?", "symbol": "AAPL"})
    assert r.status_code == 200
    assert "answer" in r.json()
