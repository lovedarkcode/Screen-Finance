"""Financial statements service: P&L, balance sheet, cash flow, ratios."""
from __future__ import annotations


class FinancialService:
    async def get_quarters(self, symbol: str) -> dict:
        return {"columns": [], "rows": []}

    async def get_profit_loss(self, symbol: str) -> dict:
        return {"items": []}

    async def get_balance_sheet(self, symbol: str) -> dict:
        return {"items": []}

    async def get_cash_flow(self, symbol: str) -> dict:
        return {"items": []}

    async def get_ratios(self, symbol: str) -> dict:
        return {"items": []}
