"""Earnings release parser."""
from __future__ import annotations


class EarningsParser:
    async def parse(self, raw: str) -> dict:
        return {"highlights": [], "guidance": None, "financials": {}}
