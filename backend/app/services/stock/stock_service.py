"""Core stock domain service: lookup, metadata, prices."""
from __future__ import annotations


class StockService:
    async def get_by_symbol(self, symbol: str) -> dict | None:
        return None

    async def list_stocks(self, limit: int = 25, offset: int = 0) -> list[dict]:
        return []

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        return []
