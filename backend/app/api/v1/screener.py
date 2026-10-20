"""Authenticated, read-only stock screening endpoints."""
import logging
from asyncpg import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from app.agents.screener.graph import screener_graph
from app.dependencies import require_user
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.user import User
from app.schemas.screener import ExecuteRequest, ScreenResponse, SearchRequest
from app.services.screener.cache import rate_limit
from app.services.screener.metrics import METRICS, SCHEMA_VERSION
from app.services.screener.query_builder import market_expression

router = APIRouter(prefix="/screener", tags=["screener"])
logger = logging.getLogger("screen-finance.database")


async def screening_db():
    async with SessionLocal() as session:
        try:
            if session.bind.dialect.name == "postgresql":
                await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
                await session.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            yield session
        except (SQLAlchemyError, PostgresError, OSError, TimeoutError) as error:
            original = getattr(error, "orig", error)
            sqlstate = getattr(original, "sqlstate", None)
            # Exception strings/tracebacks may contain SQL, parameters or credentials.
            logger.error("Read-only database request failed: error_type=%s sqlstate=%s", type(error).__name__, sqlstate)
            if sqlstate in ("42P01", "42703"):
                raise HTTPException(503, "The database schema is out of date. Run alembic upgrade head against the deployed DATABASE_URL.") from None
            raise HTTPException(503, "The screening database is unavailable. Please retry or contact the administrator.") from None


@router.post("/search", response_model=ScreenResponse)
async def search(payload: SearchRequest, user: User = Depends(require_user), session=Depends(screening_db)):
    await rate_limit(user)
    state = await screener_graph.ainvoke({"query": payload.query, "session": session, "page": payload.page}, config={"recursion_limit": 8})
    return state["result"]


@router.post("/execute", response_model=ScreenResponse)
async def execute(payload: ExecuteRequest, user: User = Depends(require_user), session=Depends(screening_db)):
    await rate_limit(user)
    state = await screener_graph.ainvoke({"draft": payload.screen, "original_query": payload.original_query, "session": session, "page": payload.page}, config={"recursion_limit": 8})
    return state["result"]


@router.get("/metrics")
async def metrics():
    return {"version": SCHEMA_VERSION, "metrics": [{"field": key, **{name: value for name, value in info.items() if name != "column"}} for key, info in METRICS.items()]}


@router.get("/sectors")
async def sectors(session=Depends(screening_db)):
    market = market_expression()
    rows = (await session.execute(select(market, Stock.sector, func.count()).where(Stock.sector.is_not(None)).group_by(market, Stock.sector).order_by(Stock.sector))).all()
    industries = (await session.execute(select(market, Stock.industry, func.count()).where(Stock.industry.is_not(None)).group_by(market, Stock.industry).order_by(Stock.industry))).all()
    return {"sectors": [{"market": market, "name": sector, "count": count} for market, sector, count in rows], "industries": [{"market": market, "name": industry, "count": count} for market, industry, count in industries]}


@router.post("/run", response_model=ScreenResponse)
async def run_screener(payload: SearchRequest, user: User = Depends(require_user), session=Depends(screening_db)):
    return await search(payload, user, session)


@router.get("/presets")
async def list_presets() -> list[dict]:
    return [
        {"id": "high_roe",     "name": "High ROE",            "query": "ROE > 20"},
        {"id": "low_pe",       "name": "Low P/E",             "query": "P/E < 15"},
        {"id": "growth_value", "name": "Growth at Reasonable Value", "query": "ROE > 15 AND P/E < 25"},
    ]


@router.post("/save")
async def save_screen(_user: User = Depends(require_user)):
    raise HTTPException(501, "Saved natural-language screens are not available yet.")
