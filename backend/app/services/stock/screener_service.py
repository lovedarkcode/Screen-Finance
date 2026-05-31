"""Screener: run user-defined queries against the stock universe."""
from __future__ import annotations


class ScreenerService:
    async def run(self, query: str, filters: dict | None = None, limit: int = 50) -> list[dict]:
        return []

    async def list_presets(self) -> list[dict]:
        return []
