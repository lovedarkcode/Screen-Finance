"""Finnhub data adapter."""
from __future__ import annotations

from app.config import settings


class FinnhubService:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY

    async def get_quote(self, symbol: str) -> dict:
        return {"symbol": symbol, "source": "Finnhub"}

    async def get_news(self, symbol: str) -> list[dict]:
        return []
