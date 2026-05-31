"""Portfolio endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class Holding(BaseModel):
    symbol: str
    quantity: float
    avg_price: float


@router.get("")
async def get_portfolio() -> dict:
    return {"holdings": [], "total_value": 0.0, "total_pnl": 0.0}


@router.post("/holdings")
async def add_holding(holding: Holding) -> Holding:
    return holding


@router.delete("/holdings/{symbol}")
async def remove_holding(symbol: str) -> dict:
    return {"removed": symbol}


@router.get("/performance")
async def performance(range: str = "1Yr") -> dict:
    return {"range": range, "series": []}
