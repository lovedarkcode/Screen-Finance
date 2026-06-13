"""Watchlist endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_user
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("")
async def list_watchlist(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Watchlist.symbol).where(Watchlist.user_id == current_user.id)
    )
    symbols = [row[0] for row in result.all()]
    return {"items": symbols}


@router.post("/{symbol}")
async def add_to_watchlist(
    symbol: str,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol_upper = symbol.strip().upper()
    stmt = select(Watchlist).where(
        Watchlist.user_id == current_user.id, Watchlist.symbol == symbol_upper
    )
    existing = await db.scalar(stmt)
    if not existing:
        watchlist_item = Watchlist(user_id=current_user.id, symbol=symbol_upper)
        db.add(watchlist_item)
        await db.commit()
    return {"added": symbol_upper}


@router.delete("/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol_upper = symbol.strip().upper()
    stmt = delete(Watchlist).where(
        Watchlist.user_id == current_user.id, Watchlist.symbol == symbol_upper
    )
    await db.execute(stmt)
    await db.commit()
    return {"removed": symbol_upper}

