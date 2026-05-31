"""Polygon.io data adapter."""
from __future__ import annotations

from app.config import settings


class PolygonService:
    BASE_URL = "https://api.polygon.io"

    def __init__(self) -> None:
        self.api_key = settings.POLYGON_API_KEY

    async def get_aggregates(self, symbol: str, multiplier: int = 1, timespan: str = "day") -> list[dict]:
        return []
