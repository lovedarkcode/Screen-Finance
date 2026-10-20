"""Read-only checks against the configured database and, optionally, public providers."""
import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.db.session import SessionLocal, engine
from app.services.quarterly_results import list_results
from app.services.ai.stock_analysis_service import _load_financials, _resolve_quote
from app.services.screener.ingestion import normalize_rows
from fastapi.concurrency import run_in_threadpool


async def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--probe-provider", action="store_true")
    options = args.parse_args()
    output = {"checked_at": datetime.now(UTC).isoformat(), "read_only": True}
    try:
        async with SessionLocal() as session:
            output["database"] = {market: await list_results(session, market=market, page_size=50) for market in ("IN", "US")}
    except Exception as error:
        output["database_error_type"] = type(error).__name__
    finally:
        await engine.dispose()
    if options.probe_provider:
        output["provider"] = []
        for symbol in ("AAPL", "TCS.NS"):
            try:
                quote = await _resolve_quote(symbol)
                snapshot = await run_in_threadpool(_load_financials, quote["symbol"])
                rows = normalize_rows(quote, snapshot, datetime.now(UTC))
                quarters = [row for row in rows if row["period_type"] == "quarterly"]
                output["provider"].append({"symbol": symbol, "quarterly_records": len(quarters), "latest": quarters[0] if quarters else None})
            except Exception as error:
                output["provider"].append({"symbol": symbol, "error_type": type(error).__name__})
    target = Path(__file__).with_name("live-verification.json")
    target.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"database": "database" in output, "provider": [{"symbol": row["symbol"], "quarterly_records": row.get("quarterly_records"), "error_type": row.get("error_type")} for row in output.get("provider", [])]}))


if __name__ == "__main__":
    asyncio.run(main())
