"""Read-only coverage and real example-query verification; no LLM calls."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from sqlalchemy import func, select
from app.db.session import SessionLocal, engine
from app.models.financials import Financials
from app.models.result_listing import ResultListing
from app.models.quarterly_poll_state import QuarterlyPollState
from app.models.stock import Stock
from app.agents.screener.graph import screener_graph
from app.schemas.screener import ScreenDefinition


async def main():
    engine.echo = False
    try:
        if "--refresh-index" in sys.argv:
            from app.services.screener.indexes import sync_sp500
            print(json.dumps({"index_refresh": await sync_sp500()}))
        async with SessionLocal() as session:
            result = (await screener_graph.ainvoke({"draft": ScreenDefinition(market="IN", filters=[
                {"field": "revenue_growth", "operator": "gt", "value": 5},
                {"field": "pe", "operator": "lt", "value": 25},
            ]), "session": session, "page": 1}))["result"]
            checked = (await session.execute(select(func.count()).where(ResultListing.screener_checked_at.is_not(None)))).scalar_one()
            covered = (await session.execute(select(func.count(func.distinct(Financials.stock_id))))).scalar_one()
            state = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "screener"))).scalar_one_or_none()
            index = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "screener_sp500"))).scalar_one_or_none()
            for row in result["stocks"]:
                assert row["metrics"]["revenue_growth:annual"]["value"] > 5
                assert 0 < row["metrics"]["pe:ttm"]["value"] < 25
            ai = []
            if "--ai" in sys.argv:
                for query, market in [("Show companies with revenue growth above 5% and P/E below 25.", "IN"),
                                      ("Show S&P 500 companies with P/E below 25.", "US")]:
                    response = (await screener_graph.ainvoke({"query": query, "market": market, "session": session, "page": 1}))["result"]
                    ai.append({"query": query, "status": response["status"], "matches": response["total_count"], "clarification": response["clarification"]})
                    if response["status"] == "success":
                        assert response["parsed_filters"]["market"] == market
            print(json.dumps({"listings": (await session.execute(select(func.count(Stock.id)))).scalar_one(),
                "financial_coverage": covered, "refresh_attempted": checked,
                "matches": result["total_count"], "eligible": result["eligible_count"],
                "symbols": [row["symbol"] for row in result["stocks"]],
                "worker_status": (state or {}).get("status"), "sp500": (state or {}).get("sp500"),
                "index_members": len((index or {}).get("symbols", [])), "ai": ai}, indent=2))
    finally:
        await engine.dispose()


asyncio.run(main())
