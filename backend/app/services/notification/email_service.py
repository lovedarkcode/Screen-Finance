"""Email delivery service (SMTP/SendGrid/Resend)."""
from __future__ import annotations


class EmailService:
    async def send(self, to: str, subject: str, body: str, html: str | None = None) -> bool:
        return True
