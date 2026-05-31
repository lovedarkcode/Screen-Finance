"""Earnings-call transcript parser."""
from __future__ import annotations


class TranscriptParser:
    async def parse(self, raw: str) -> dict:
        return {"speakers": [], "qna": [], "prepared_remarks": []}
