"""Embeddings service: text → vector."""
from __future__ import annotations


class EmbeddingsService:
    async def embed(self, text: str) -> list[float]:
        return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[] for _ in texts]
