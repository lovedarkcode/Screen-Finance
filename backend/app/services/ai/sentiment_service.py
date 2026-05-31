"""Sentiment analysis service for news/transcripts."""
from __future__ import annotations


class SentimentService:
    async def analyze(self, text: str) -> dict:
        return {"score": 0.0, "label": "neutral"}
