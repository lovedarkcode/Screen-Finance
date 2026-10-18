"""Authentication regressions use isolated users, never the configured database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.dependencies import get_db
from app.core.security import hash_password
from app.models.user import User

PASSWORD = "fixture-password"


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "isolated-auth-test-signing-key-at-least-32-bytes")
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    User.__table__.create(engine)
    with Session(engine) as session:
        session.add(User(name="Existing fixture", email="existing@example.com", password_hash=hash_password(PASSWORD), provider="local"))
        session.commit()

        class TestSession:
            async def scalar(self, statement):
                return session.scalar(statement)

            def add(self, value):
                session.add(value)

            async def commit(self):
                session.commit()

            async def refresh(self, value):
                session.refresh(value)

        app.dependency_overrides[get_db] = lambda: TestSession()
        try:
            yield TestClient(app)
        finally:
            app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_login_returns_token(auth_client):
    response = auth_client.post("/api/v1/auth/login", json={"email": "existing@example.com", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["access_token"] and response.json()["token_type"] == "bearer"
    assert response.json()["user"]["email"] == "existing@example.com"
    assert auth_client.post("/api/v1/auth/login", json={"email": "existing@example.com", "password": "wrong-password"}).status_code == 401


def test_register_returns_token(auth_client):
    response = auth_client.post("/api/v1/auth/register", json={"email": "new@example.com", "password": PASSWORD, "name": "New fixture"})
    assert response.status_code == 201
    assert response.json()["access_token"] and response.json()["user"]["email"] == "new@example.com"
    assert auth_client.post("/api/v1/auth/register", json={"email": "short@example.com", "password": "pw", "name": "Invalid"}).status_code == 422
