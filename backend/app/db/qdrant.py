"""Qdrant vector DB client."""
from __future__ import annotations

from qdrant_client import QdrantClient

from app.config import settings

_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL)
    return _client
