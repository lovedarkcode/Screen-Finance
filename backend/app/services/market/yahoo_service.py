"""Yahoo Finance data adapter (via yfinance)."""
from __future__ import annotations


class YahooService:
    async def get_quote(self, symbol: str) -> dict:
        return {"symbol": symbol, "source": "Yahoo"}

    async def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
        return []
