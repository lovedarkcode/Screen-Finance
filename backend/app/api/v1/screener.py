"""Stock screener endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/screener", tags=["screener"])


class ScreenerQuery(BaseModel):
    query: str
    filters: dict | None = None
    limit: int = 50


@router.post("/run")
async def run_screener(payload: ScreenerQuery) -> dict:
    return {"query": payload.query, "results": [], "total": 0}


@router.get("/presets")
async def list_presets() -> list[dict]:
    return [
        {"id": "high_roe",     "name": "High ROE",            "query": "ROE > 20"},
        {"id": "low_pe",       "name": "Low P/E",             "query": "P/E < 15"},
        {"id": "growth_value", "name": "Growth at Reasonable Value", "query": "ROE > 15 AND P/E < 25"},
    ]


@router.post("/save")
async def save_screen(name: str, payload: ScreenerQuery) -> dict:
    return {"id": "stub", "name": name, "query": payload.query}
