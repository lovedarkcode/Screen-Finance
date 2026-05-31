"""AI summary service: generate company / earnings / news summaries."""
from __future__ import annotations


class AISummaryService:
    async def summarize_company(self, symbol: str) -> dict:
        return {"symbol": symbol, "summary": "", "keyPoints": []}

    async def summarize_earnings(self, symbol: str, period: str) -> dict:
        return {"symbol": symbol, "period": period, "summary": ""}
