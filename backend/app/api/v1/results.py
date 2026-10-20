"""Authenticated quarterly results from the existing imported financial evidence."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.screener import screening_db
from app.dependencies import require_user
from app.services.quarterly_results import list_results

router = APIRouter(prefix="/results", tags=["quarterly results"], dependencies=[Depends(require_user)])


@router.get("/imported")
async def results(
    market: Literal["IN", "US", "ALL"] = "IN",
    quarter: date | None = None,
    industry: str | None = Query(default=None, max_length=150),
    q: str = Query(default="", max_length=100),
    sort: Literal["latest", "name", "sales_growth", "profit_growth"] = "latest",
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=12, ge=1, le=50),
    session=Depends(screening_db),
):
    return await list_results(session, market=market, quarter=quarter, industry=industry, q=q.strip(), sort=sort, page=page, page_size=page_size)
