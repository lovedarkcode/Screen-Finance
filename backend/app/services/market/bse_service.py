"""BSE (Bombay Stock Exchange) data adapter."""
from __future__ import annotations


class BSEService:
    BASE_URL = "https://api.bseindia.com"

    async def get_quote(self, symbol: str) -> dict:
        return {"symbol": symbol, "source": "BSE"}
