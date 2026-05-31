"""Qdrant collection definitions and creation helpers."""
from __future__ import annotations

COLLECTIONS = {
    "filings":     {"size": 1536, "distance": "Cosine"},
    "news":        {"size": 1536, "distance": "Cosine"},
    "transcripts": {"size": 1536, "distance": "Cosine"},
    "reports":     {"size": 1536, "distance": "Cosine"},
}


def ensure_collection(name: str) -> dict:
    return {"collection": name, "spec": COLLECTIONS.get(name, {})}
