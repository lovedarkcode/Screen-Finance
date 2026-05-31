"""Price / news alert engine."""
from __future__ import annotations


class AlertService:
    async def evaluate(self, symbol: str) -> list[dict]:
        return []

    async def create(self, user_id: int, rule: dict) -> dict:
        return {"id": 0, "user_id": user_id, **rule}
