"""Watchlist endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("")
async def list_watchlist() -> dict:
    return {"items": []}


@router.post("/{symbol}")
async def add_to_watchlist(symbol: str) -> dict:
    return {"added": symbol}


@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str) -> dict:
    return {"removed": symbol}
