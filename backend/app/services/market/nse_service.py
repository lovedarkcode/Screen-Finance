"""NSE (National Stock Exchange of India) data adapter."""
from __future__ import annotations


class NSEService:
    BASE_URL = "https://www.nseindia.com/api"

    async def get_quote(self, symbol: str) -> dict:
        return {"symbol": symbol, "source": "NSE"}

    async def get_indices(self) -> list[dict]:
        return []
