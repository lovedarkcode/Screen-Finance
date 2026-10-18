"""Development-only, read-only diagnostics over the application's PostgreSQL session.

python scripts/diagnose_screener.py [--market IN] [--screen-file screen.json]
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import func, select, text
from app.config import settings
from app.db.session import SessionLocal, engine
from app.models.stock import Stock
from app.models.financials import Financials
from app.schemas.screener import ScreenDefinition
from app.services.screener.metrics import METRICS, VALIDATION_VERSION
from app.services.screener.query_builder import diagnostics, exchange_expression, market_expression, statements, universe_count
from app.services.screener.validator import validate_screen


async def collect(session, screen):
    market, exchange = market_expression(), exchange_expression()
    identity = dict((await session.execute(text("SELECT current_database() AS database, current_schema() AS schema, inet_server_addr()::text AS server_address, inet_server_port() AS server_port"))).mappings().one())
    _, unfiltered, _ = statements(ScreenDefinition(market=screen.market, sort_period="snapshot"), 1)
    coverage = {}
    for field, info in METRICS.items():
        if field == "market_cap":
            coverage[field] = {"snapshot": (await session.execute(select(func.count(Stock.id)).where(Stock.market_cap.is_not(None)))).scalar_one()}
        else:
            rows = (await session.execute(select(Financials.period_type, func.count(func.distinct(Financials.stock_id))).where(Financials.validation_version == VALIDATION_VERSION, getattr(Financials, info["column"]).is_not(None), Financials.provenance[field]["validation_status"].as_string().in_(["provider", "normalized", "recomputed"])).group_by(Financials.period_type))).all()
            coverage[field] = dict(rows)
    periods = (await session.execute(select(Financials.period_type, Financials.currency, func.count().label("records"), func.min(Financials.period_end).label("earliest"), func.max(Financials.period_end).label("latest")).group_by(Financials.period_type, Financials.currency))).mappings().all()
    return {
        "database_connected": True,
        "connection": identity,
        "total_stocks": await universe_count(session, None),
        "total_financial_records": (await session.execute(select(func.count(Financials.id)))).scalar_one(),
        "stocks_with_financials": (await session.execute(select(func.count(func.distinct(Financials.stock_id))))).scalar_one(),
        "unfiltered_stock_count": (await session.execute(unfiltered)).scalar_one(),
        "market_counts": dict((await session.execute(select(market, func.count()).group_by(market))).all()),
        "exchange_counts": dict((await session.execute(select(exchange, func.count()).group_by(exchange))).all()),
        "metric_coverage": coverage,
        "reporting_periods": [dict(row) for row in periods],
        "screen": screen.model_dump(mode="json"),
        "filter_trace": await diagnostics(session, screen),
    }


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market", choices=["IN", "US"])
    parser.add_argument("--period-end", help="Exact fiscal end for filters in --screen-file")
    parser.add_argument("--screen-file", type=Path)
    args = parser.parse_args()
    if settings.ENVIRONMENT != "development":
        parser.error("Filter diagnostics are available only in the development environment.")
    draft = ScreenDefinition.model_validate_json(args.screen_file.read_text(encoding="utf-8")) if args.screen_file else ScreenDefinition(market=args.market)
    if args.period_end:
        if not draft.filters:
            parser.error("--period-end requires financial filters in --screen-file")
        draft = ScreenDefinition.model_validate({**draft.model_dump(), "filters": [{**item.model_dump(), "period_end": args.period_end} for item in draft.filters]})
    screen, _ = validate_screen(draft)
    engine.echo = False
    connected = False
    try:
        async with SessionLocal() as session:
            await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            connected = True
            await session.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            result = await collect(session, screen)
    except Exception as error:
        print(json.dumps({"database_connected": connected, "error_type": type(error).__name__}))
        return 1
    finally:
        await engine.dispose()
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
