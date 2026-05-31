"""Vector indexing helpers."""
from __future__ import annotations


async def upsert(collection: str, points: list[dict]) -> int:
    return len(points)


async def delete_by_filter(collection: str, where: dict) -> int:
    return 0
