"""AI / RAG Pydantic schemas."""
from pydantic import BaseModel


class ChatIn(BaseModel):
    message: str
    symbol: str | None = None


class ChatOut(BaseModel):
    answer: str
    sources: list[dict] = []


class SummaryOut(BaseModel):
    symbol: str
    summary: str
    keyPoints: list[str]
