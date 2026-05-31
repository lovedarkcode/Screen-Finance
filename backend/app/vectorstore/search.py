"""Vector search helpers."""
from __future__ import annotations


async def search(collection: str, vector: list[float], top_k: int = 5, filters: dict | None = None) -> list[dict]:
    return []


async def hybrid_search(collection: str, query: str, vector: list[float], top_k: int = 5) -> list[dict]:
    return []
