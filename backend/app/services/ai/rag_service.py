"""RAG orchestration: retrieve relevant docs and answer questions."""
from __future__ import annotations


class RAGService:
    async def answer(self, question: str, symbol: str | None = None, top_k: int = 5) -> dict:
        return {"answer": "", "sources": [], "symbol": symbol}
