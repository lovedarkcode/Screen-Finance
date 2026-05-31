"""Portfolio Pydantic schemas."""
from pydantic import BaseModel


class HoldingIn(BaseModel):
    symbol: str
    quantity: float
    avg_price: float


class HoldingOut(HoldingIn):
    id: int


class PortfolioOut(BaseModel):
    holdings: list[HoldingOut]
    total_value: float
    total_pnl: float
