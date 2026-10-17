"""Optional live Yahoo smoke check. Run from backend with the existing Python environment."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.api.v1 import stocks


async def main():
    checks = []
    for symbol in ["AAPL", "MSFT", "BRK-B", "F", "TCS.NS"]:
        try:
            result = await stocks.get_stock(symbol)
            checks.append({"symbol": symbol, "ok": result["price"] is not None, "exchange": result["exchange"], "currency": result["currency"]})
        except Exception as exc:
            checks.append({"symbol": symbol, "ok": False, "error": str(exc)})
    for query in ["Apple", "Microsoft", "F", "TCS"]:
        try:
            result = await stocks.list_stocks(q=query, limit=8)
            checks.append({"query": query, "ok": bool(result["items"]), "symbols": [item["symbol"] for item in result["items"]]})
        except Exception as exc:
            checks.append({"query": query, "ok": False, "error": str(exc)})
    for endpoint in ["overview", "quarters", "shareholding"]:
        try:
            result = await asyncio.wait_for(getattr(stocks, f"get_{endpoint}")("AAPL"), timeout=90)
            count = len(result) if isinstance(result, list) else len(result.get("metrics", result.get("rows", [])))
            checks.append({"symbol": "AAPL", "endpoint": endpoint, "ok": count > 0, "items": count, "currency": result.get("currency") if isinstance(result, dict) else None})
        except Exception as exc:
            checks.append({"symbol": "AAPL", "endpoint": endpoint, "ok": False, "error": str(exc)})
    print(json.dumps(checks, indent=2), flush=True)
    if not all(check["ok"] for check in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
