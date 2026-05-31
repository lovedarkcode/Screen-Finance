"""Web push notifications (FCM / OneSignal)."""
from __future__ import annotations


class PushService:
    async def send(self, user_id: int, title: str, body: str, data: dict | None = None) -> bool:
        return True
