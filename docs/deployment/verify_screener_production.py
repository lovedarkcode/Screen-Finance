"""Exercise deployed auth, natural-language screens and pagination, then clean up."""
import json
import secrets
from pathlib import Path

import httpx
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://assest-hunter.vercel.app"
EMAIL = f"discovery-check-{secrets.token_hex(8)}@example.com"
checks = []


def check(name, condition, **details):
    checks.append({"check": name, "passed": bool(condition), **details})
    print(json.dumps(checks[-1]), flush=True)
    assert condition, name


def main():
    production = dotenv_values(ROOT / ".vercel/results-production.env")
    database = create_engine(make_url(production.get("DATABASE_URL_UNPOOLED") or production["DATABASE_URL"]).set(drivername="postgresql+psycopg2"), connect_args={"connect_timeout": 15})
    try:
        with httpx.Client(base_url=BASE, timeout=120) as client:
            health = client.get("/api/health/db")
            check("Hosted database", health.status_code == 200 and health.json().get("status") == "ok")
            metrics = client.get("/api/v1/screener/metrics")
            check("Deployed screener version", metrics.status_code == 200 and metrics.json().get("version") == "screener-v5")
            unauthorized = client.post("/api/v1/screener/search", json={"query": "Show companies", "market": "IN"})
            check("Authentication enforced", unauthorized.status_code == 401)
            response = client.post("/api/v1/auth/register", json={"name": "Temporary deployment check", "email": EMAIL, "password": secrets.token_urlsafe(24)})
            check("Verification account", response.status_code == 201)
            client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
            queries = [("Indian growth and value", "Show companies with revenue growth above 5% and P/E below 25.", "IN"),
                       ("S&P 500", "Show S&P 500 companies with P/E below 25.", "US")]
            for name, query, market in queries:
                response = client.post("/api/v1/screener/search", json={"query": query, "market": market})
                data = response.json()
                check(name, response.status_code == 200 and data.get("status") == "success" and data.get("total_count", 0) > 3,
                      http=response.status_code, matches=data.get("total_count"), universe=data.get("universe_count"), eligible=data.get("eligible_count"))
                check(name + " market", data["parsed_filters"]["market"] == market and all(row["market"] == market for row in data["stocks"]))
                for row in data["stocks"]:
                    assert 0 < row["metrics"]["pe:ttm"]["value"] < 25
                    if market == "IN":
                        assert row["metrics"]["revenue_growth:annual"]["value"] > 5
                if market == "US":
                    assert data["parsed_filters"]["index"] == "SP500"
                    with database.connect() as connection:
                        members = connection.scalar(text("select payload from quarterly_poll_state where name = 'screener_sp500'"))["symbols"]
                    assert all(row["symbol"] in members for row in data["stocks"])
                if data["total_count"] > data["page_size"]:
                    page = client.post("/api/v1/screener/execute", json={"screen": data["parsed_filters"], "page": 2, "original_query": query})
                    page_data = page.json()
                    check(name + " pagination", page.status_code == 200 and page_data["page"] == 2 and bool(page_data["stocks"]))
            conflict = client.post("/api/v1/screener/search", json={"query": "Show US companies with P/E below 25.", "market": "IN"}).json()
            check("Conflicting market is explained", conflict.get("status") != "success" and bool(conflict.get("clarification")))
            with database.connect() as connection:
                check("Production schema", connection.scalar(text("select version_num from alembic_version")) == "f1d53c6249ea")
    finally:
        with database.begin() as connection:
            connection.execute(text("DELETE FROM users WHERE email = :email"), {"email": EMAIL})
        database.dispose()
        (ROOT / "docs/deployment/screener-verification.json").write_text(json.dumps({"url": BASE, "checks": checks}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"verification_error": type(error).__name__}))
        raise SystemExit(1) from None
