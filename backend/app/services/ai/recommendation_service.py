"""AI recommendation service: BUY/HOLD/SELL ratings with rationale."""
from __future__ import annotations


class RecommendationService:
    async def recommend(self, symbol: str) -> dict:
        return {"symbol": symbol, "rating": "HOLD", "confidence": 0.0, "rationale": []}
