"""AI / RAG / agent endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str
    symbol: str | None = None


class SummaryRequest(BaseModel):
    symbol: str


@router.post("/chat")
async def chat(payload: ChatRequest) -> dict:
    return {
        "answer": f"(stub) You asked: {payload.message}",
        "symbol": payload.symbol,
        "sources": [],
    }


@router.get("/summary/{symbol}")
async def ai_summary(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "summary": (
            "Apple Inc. is a global technology leader specializing in iPhone, Mac, iPad, "
            "Wearables and Services. Strong brand, high customer loyalty and consistent "
            "financial performance drive long-term value."
        ),
        "keyPoints": [
            "Strong ecosystem and brand loyalty",
            "Services segment growing rapidly",
            "Robust cash flows and profitability",
            "Exposure to China remains a key risk",
            "Innovation in AI and wearables to watch",
        ],
    }


@router.get("/recommendations/{symbol}")
async def recommendations(symbol: str) -> dict:
    return {"symbol": symbol, "rating": "BUY", "confidence": 0.78, "rationale": []}


@router.get("/agents")
async def list_agents() -> list[dict]:
    return [
        {"id": "financial_analyst", "name": "Financial Analyst"},
        {"id": "valuation_agent",   "name": "Valuation Agent"},
        {"id": "news_agent",        "name": "News Agent"},
        {"id": "sec_agent",         "name": "SEC Filings Agent"},
        {"id": "portfolio_agent",   "name": "Portfolio Agent"},
    ]


@router.post("/compare")
async def compare(symbols: list[str]) -> dict:
    return {"symbols": symbols, "summary": "(stub) comparison"}
