"""News endpoints."""
from fastapi import APIRouter, Query
from app.services.news_service import market_news

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def get_news(symbol: str | None = Query(default=None, max_length=40), limit: int = Query(default=20, ge=1, le=50)) -> dict:
    return await market_news(symbol, limit)


@router.get("/trending")
async def trending_news(limit: int = Query(default=10, ge=1, le=50)) -> dict:
    # Latest market headlines; no popularity score is supplied by this feed.
    return await market_news(None, limit)
