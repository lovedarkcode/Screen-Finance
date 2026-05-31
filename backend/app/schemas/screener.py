"""Screener Pydantic schemas."""
from pydantic import BaseModel


class ScreenerIn(BaseModel):
    query: str
    filters: dict | None = None
    limit: int = 50


class ScreenerRow(BaseModel):
    symbol: str
    name: str
    metrics: dict


class ScreenerOut(BaseModel):
    query: str
    results: list[ScreenerRow]
    total: int
