"""Tests for /api/v1/auth endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_returns_token() -> None:
    r = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "pw"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_register_returns_token() -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "pw", "name": "A"},
    )
    assert r.status_code == 201
    assert "access_token" in r.json()
