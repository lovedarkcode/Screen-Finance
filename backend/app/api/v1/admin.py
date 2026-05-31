"""Admin endpoints (data pipelines, AI controls)."""
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pipelines")
async def list_pipelines() -> list[dict]:
    return [
        {"id": "stock_sync",  "name": "Stock Sync",     "status": "idle"},
        {"id": "news_sync",   "name": "News Sync",      "status": "idle"},
        {"id": "embeddings",  "name": "Embeddings Job", "status": "idle"},
        {"id": "sec_filings", "name": "SEC Filings",    "status": "idle"},
    ]


@router.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str) -> dict:
    return {"pipeline": pipeline_id, "status": "queued"}


@router.get("/ai-controls")
async def ai_controls() -> dict:
    return {"models": [], "prompts": [], "limits": {}}
