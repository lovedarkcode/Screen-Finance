"""Read-only public financial dataset audit; no credentials or SQL in output."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from sqlalchemy import func, select, text
from app.db.session import SessionLocal, engine
from app.models.stock import Stock
from app.models.financials import Financials
from app.schemas.screener import ScreenDefinition
from app.services.screener import query_builder
from app.services.screener.validator import validate_screen


async def main():
    engine.echo = False
    result = {}
    async with SessionLocal() as session:
        await session.execute(text("SET TRANSACTION READ ONLY"))
        result["stock_rows"] = (await session.execute(select(func.count(Stock.id)))).scalar_one()
        result["financial_rows"] = (await session.execute(select(func.count(Financials.id)))).scalar_one()
        result["markets"] = [dict(row._mapping) for row in (await session.execute(select(Stock.country.label("market"), func.count().label("imported")).group_by(Stock.country))).all()]
        result["sectors"] = [dict(row._mapping) for row in (await session.execute(select(Stock.country.label("market"), Stock.sector, func.count().label("imported")).group_by(Stock.country, Stock.sector))).all()]
        for market in ["IN", "US"]:
            screen, _ = validate_screen(ScreenDefinition(market=market))
            statement, _, selections = query_builder.statements(screen, 1)
            result[market] = {"universe_count": await query_builder.universe_count(session, market), "stocks": query_builder.format_rows((await session.execute(statement)).all(), screen, selections)}
        result["diagnostics"] = {}
        for label, end in [("latest", None), ("exact_reported_date", "2026-10-18")]:
            screen, _ = validate_screen(ScreenDefinition(market="IN", sector="Energy", filters=[{"field": "revenue_growth", "operator": "gt", "value": 15, "period": "annual", "period_end": end}, {"field": "pe", "operator": "lt", "value": 20, "period": "ttm", "period_end": end}]))
            result["diagnostics"][label] = await query_builder.diagnostics(session, screen)
    await engine.dispose()
    destination = Path(__file__).with_name("database-audit.json")
    destination.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    summary = {key: result[key] for key in ["stock_rows", "financial_rows", "markets", "sectors"]}
    summary["indian_metrics"] = [{"symbol": stock["symbol"], "sector": stock["sector"], "growth": stock["metrics"]["revenue_growth:annual"], "pe": stock["metrics"]["pe:ttm"]} for stock in result["IN"]["stocks"]]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
