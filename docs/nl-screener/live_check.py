"""Read-only live API checks with isolated in-process authentication.

Uses the real configured PostgreSQL data and NVIDIA. Does not create users,
change deployed authentication, or write financial records. --no-ai skips NVIDIA.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import require_user
from app.db.session import engine
from app.config import settings


def verify_matches(data):
    screen = data["parsed_filters"]
    for stock in data["stocks"]:
        assert stock["market"] == screen["market"]
        if screen["sector"]:
            assert stock["sector"].casefold() == screen["sector"].casefold()
        if screen["exchange"]:
            assert stock["exchange"] == screen["exchange"]
        if screen.get("exchanges"):
            assert stock["exchange"] in screen["exchanges"]
        for condition in screen["filters"]:
            key = f"{condition['field']}:{condition['period']}"
            if condition["period_end"]:
                key += ":" + condition["period_end"]
            metric = stock["metrics"][key]
            actual, threshold = metric["value"], condition["value"]
            assert actual is not None and metric["validation_status"]
            comparisons = {"gt": lambda: actual > threshold, "gte": lambda: actual >= threshold, "lt": lambda: actual < threshold, "lte": lambda: actual <= threshold, "eq": lambda: actual == threshold, "between": lambda: threshold[0] <= actual <= threshold[1]}
            assert comparisons[condition["operator"]]()
            if condition["currency"]:
                assert metric["currency"] == condition["currency"]
            if condition["period_end"]:
                assert metric["period_end"] == condition["period_end"]


def main():
    tag = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--tag=")), "")
    suffix = "-" + tag if tag.isalnum() else ""
    engine.echo = False
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=-1)
    checks = []
    failed = False
    try:
        with TestClient(app) as client:
            for market in ["US", "IN"]:
                screen = {"market": market, "filters": [{"field": "roe", "operator": "gt", "value": 0}], "sort_by": "market_cap", "limit": 10}
                response = client.post("/api/v1/screener/execute", json={"screen": screen})
                data = response.json()
                result = {"kind": "execute", "market": market, "http": response.status_code, "matches": data.get("total_count"), "universe_count": data.get("universe_count")}
                if response.status_code == 200:
                    verify_matches(data)
                    (Path(__file__).parent / f"live-execute-{market}{suffix}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
                else:
                    failed = True
                    result["detail"] = data.get("detail")
                checks.append(result)
                print(json.dumps(result), flush=True)
            if "--no-ai" not in sys.argv:
                queries = ["Find US technology companies with ROE above 20% and debt-to-equity below 0.5.", "Show Indian companies with revenue growth above 15% and P/E below 25.", "Find profitable US companies with market capitalization above $10 billion."]
                if "--energy" in sys.argv:
                    queries = ["Find Indian Energy companies with annual revenue growth above 15% and trailing P/E below 20.", "Find Indian Energy companies with annual revenue growth above 5% and trailing P/E below 25."]
                if "--india" in sys.argv:
                    queries = ["Show Indian companies with revenue growth above 15% and P/E below 25.", "Show Indian companies with revenue growth above 5% and P/E below 25."]
                if "--exchanges" in sys.argv:
                    queries = ["Find Indian companies listed on NSE or BSE with Return on Equity (ROE) greater than 15%, debt-to-equity ratio below 1, annual revenue growth above 10%, positive net profit margin, and P/E ratio below 30. Sort the results by market capitalization in descending order and show the top 20 companies.", "Find Indian companies on NSE or BSE with annual revenue growth above 5% and P/E below 25."]
                for query in queries:
                    response = client.post("/api/v1/screener/search", json={"query": query})
                    data = response.json()
                    result = {"kind": "search", "model": settings.NVIDIA_SCREENER_MODEL or settings.NVIDIA_MODEL, "http": response.status_code, "status": data.get("status"), "matches": data.get("total_count"), "detail": data.get("detail") or data.get("clarification")}
                    failed |= response.status_code != 200 or data.get("status") != "success"
                    if response.status_code == 200 and data.get("status") == "success":
                        verify_matches(data)
                        assert data["original_query"] == query
                        if "--exchanges" in sys.argv:
                            screen = data["parsed_filters"]
                            assert set(screen["exchanges"]) == {"NSE", "BSE"}
                            assert screen["market"] == "IN" and screen["sector"] is None
                            if "top 20" in query:
                                assert screen["limit"] == 20 and screen["sort_by"] == "market_cap" and screen["sort_desc"]
                                assert {(f["field"], f["operator"], f["value"]) for f in screen["filters"]} == {("roe", "gt", 15), ("debt_to_equity", "lt", 1), ("revenue_growth", "gt", 10), ("net_profit_margin", "gt", 0), ("pe", "lt", 30)}
                        assert all(condition["period_end"] is None for condition in data["parsed_filters"]["filters"])
                        if "--india" in sys.argv:
                            assert data["parsed_filters"]["market"] == "IN" and data["parsed_filters"]["sector"] is None
                        replay = client.post("/api/v1/screener/execute", json={"screen": data["parsed_filters"], "original_query": query}).json()
                        assert replay["original_query"] == query and replay["total_count"] == data["total_count"]
                    checks.append(result)
                    print(json.dumps(result), flush=True)
                    (Path(__file__).parent / f"live-search-{len(checks)}{suffix}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    finally:
        app.dependency_overrides.pop(require_user, None)
    (Path(__file__).parent / f"live-verification{suffix}.json").write_text(json.dumps({"isolatedAuthentication": True, "model": settings.NVIDIA_SCREENER_MODEL or settings.NVIDIA_MODEL, "checks": checks}, indent=2), encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
