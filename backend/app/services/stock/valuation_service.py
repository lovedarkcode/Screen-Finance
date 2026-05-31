"""Valuation models: DCF, multiples, PEG, intrinsic value."""
from __future__ import annotations


class ValuationService:
    async def dcf(self, symbol: str, assumptions: dict | None = None) -> dict:
        return {"symbol": symbol, "intrinsic_value": None}

    async def multiples(self, symbol: str) -> dict:
        return {"symbol": symbol, "pe": None, "pb": None, "ev_ebitda": None}
