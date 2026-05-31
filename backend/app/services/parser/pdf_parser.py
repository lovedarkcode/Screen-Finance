"""Generic PDF parser for annual reports / filings."""
from __future__ import annotations

from pathlib import Path


class PDFParser:
    async def parse(self, path: str | Path) -> dict:
        return {"path": str(path), "pages": [], "text": ""}
