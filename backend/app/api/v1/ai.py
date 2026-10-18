"""AI / RAG / agent endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import require_user
from app.models.user import User
from app.schemas.ai import AnalysisRequest, StockAnalysisReport
from app.services.ai.stock_analysis_service import analyze_stock

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


@router.post("/analyze", response_model=StockAnalysisReport)
async def analyze(payload: AnalysisRequest, _user: User = Depends(require_user)) -> StockAnalysisReport:
    return await analyze_stock(payload.symbol)


@router.get("/summary/{symbol}")
async def ai_summary(symbol: str, _user: User = Depends(require_user)) -> dict:
    report = await analyze_stock(symbol)
    return {**report.model_dump(mode="json"), "summary": "\n\n".join(item.text for item in report.research.summary), "keyPoints": [item.text for item in report.research.strengths]}


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
