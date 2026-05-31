"""News endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def get_news(symbol: str | None = None, limit: int = 20) -> dict:
    return {"items": [], "symbol": symbol, "limit": limit}


@router.get("/trending")
async def trending_news(limit: int = 10) -> dict:
    return {"items": [], "limit": limit}
