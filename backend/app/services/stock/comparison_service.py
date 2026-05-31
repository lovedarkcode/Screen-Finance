"""Peer comparison service."""
from __future__ import annotations


class ComparisonService:
    async def peers(self, symbol: str, limit: int = 5) -> list[dict]:
        return []

    async def compare(self, symbols: list[str]) -> dict:
        return {"symbols": symbols, "matrix": []}
