"""SEC EDGAR filings parser (10-K, 10-Q, 8-K)."""
from __future__ import annotations


class SECParser:
    async def parse_10k(self, url: str) -> dict:
        return {"url": url, "type": "10-K", "sections": {}}

    async def parse_10q(self, url: str) -> dict:
        return {"url": url, "type": "10-Q", "sections": {}}
