"""Provider filings and automated summaries, separate from imported screener rows."""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.orm import aliased

from app.api.v1.screener import screening_db
from app.dependencies import require_user
from app.models.company import Company
from app.models.quarterly_result import QuarterlyResult
from app.models.quarterly_poll_state import QuarterlyPollState
from app.models.result_listing import ResultListing
from app.services.filings.yahoo import PROVIDER
from app.schemas.quarterly_filing import normalize_ticker
from app.services.filings.comparisons import comparisons
from app.services.screener.query_builder import market_expression

router = APIRouter(prefix="/results", tags=["automated quarterly filings"], dependencies=[Depends(require_user)])


class FilingOut(BaseModel):
    id: int
    provider: str
    period_basis: str
    company_id: int
    ticker: str
    company_name: str
    exchange: str
    sector: str | None
    industry: str | None
    fiscal_year: int
    quarter_period: Literal["Q1", "Q2", "Q3", "Q4"]
    period_end: date
    filing_date: date | None
    filing_date_kind: Literal["filing", "report_period_fallback", "unavailable"]
    currency: str
    revenue: Decimal | None
    net_income: Decimal | None
    eps: Decimal | None
    eps_basis: str | None
    operating_margin: Decimal | None
    first_seen_at: datetime
    updated_at: datetime
    revision: int
    ai_summary: str | None
    ai_summary_json: dict | None
    summary_status: Literal["pending", "processing", "completed", "failed"]
    summary_model: str | None
    summary_error: str | None
    comparisons: dict


class FilingsPage(BaseModel):
    items: list[FilingOut]
    total: int
    page: int
    page_size: int
    provider: str = PROVIDER
    source: str = PROVIDER
    poll_status: dict | None = None


class ListingOut(BaseModel):
    company_id: int
    ticker: str
    company_name: str
    exchange: str
    isin: str | None
    exchange_code: str
    data_status: str
    checked_at: datetime | None
    data_error: str | None
    latest_result: FilingOut | None


class LatestPage(BaseModel):
    items: list[ListingOut]
    total: int
    page: int
    page_size: int
    provider: str = PROVIDER
    source: str = PROVIDER
    date_basis: str = "Fiscal quarter end; Yahoo does not supply announcement dates here"
    coverage: dict
    catalog_status: dict | None
    poll_status: dict | None


def format_filing(company, row, history):
    return FilingOut(
        **{key: getattr(row, key) for key in FilingOut.model_fields if hasattr(row, key)},
        ticker=company.symbol, company_name=company.name, exchange=company.exchange, sector=company.sector,
        industry=company.industry, comparisons=comparisons(row, history),
    )


async def histories_for(session, pairs):
    history = defaultdict(list)
    if pairs:
        ids = {row.company_id for _, row in pairs}
        oldest_year = min(row.fiscal_year for _, row in pairs)
        rows = (await session.execute(select(QuarterlyResult).where(QuarterlyResult.company_id.in_(ids),
                                       QuarterlyResult.provider == PROVIDER,
                                       QuarterlyResult.fiscal_year >= oldest_year - 1))).scalars().all()
        for row in rows:
            history[row.company_id].append(row)
    return history


@router.get("", response_model=LatestPage)
@router.get("/latest", response_model=LatestPage)
async def latest(
    page: int = Query(default=1, ge=1, le=2000),
    page_size: int = Query(default=20, ge=1, le=100),
    market: Literal["IN", "US", "ALL"] = "ALL",
    q: str = Query(default="", max_length=100),
    exchange: Literal["NSE", "BSE", "NYSE", "NASDAQ"] | None = None,
    status: Literal["all", "ready", "pending", "unavailable", "error"] = "all",
    session=Depends(screening_db),
):
    filters = [ResultListing.active]
    if market != "ALL":
        filters.append(market_expression() == market)
    if q.strip():
        # autoescape keeps %, _ and escape characters literal in user searches.
        filters.append(Company.symbol.icontains(q.strip(), autoescape=True) | Company.name.icontains(q.strip(), autoescape=True))
    if exchange:
        filters.append(Company.exchange == exchange)
    ranked = select(QuarterlyResult, func.row_number().over(partition_by=QuarterlyResult.company_id,
        order_by=(QuarterlyResult.period_end.desc(), QuarterlyResult.id.desc())).label("position")).where(QuarterlyResult.provider == PROVIDER).subquery()
    row = aliased(QuarterlyResult, ranked)
    base = select(Company, ResultListing, row).join(ResultListing, ResultListing.company_id == Company.id).outerjoin(row, and_(row.company_id == Company.id, ranked.c.position == 1)).where(*filters)
    coverage = {"listed": 0, "with_results": 0, "pending": 0, "ready": 0, "unavailable": 0, "error": 0}
    counts = (await session.execute(select(ResultListing.status, func.count(), func.count(row.id)).select_from(Company)
        .join(ResultListing, ResultListing.company_id == Company.id).outerjoin(row, and_(row.company_id == Company.id, ranked.c.position == 1))
        .where(*filters).group_by(ResultListing.status))).all()
    for state, count, available in counts:
        coverage["listed"] += count
        coverage["with_results"] += available
        coverage[state] = count
    if status != "all":
        base = base.where(ResultListing.status == status)
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    triples = (await session.execute(base.order_by(row.period_end.desc().nullslast(), row.first_seen_at.desc().nullslast(), Company.symbol)
                                   .offset((page - 1) * page_size).limit(page_size))).all()
    pairs = [(company, result) for company, _, result in triples if result is not None]
    history = await histories_for(session, pairs)
    poll_status = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "filings"))).scalar_one_or_none()
    catalog_status = (await session.execute(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "catalog"))).scalar_one_or_none()
    return LatestPage(items=[ListingOut(company_id=company.id, ticker=company.symbol, company_name=company.name, exchange=company.exchange,
        isin=listing.isin, exchange_code=listing.exchange_code, data_status=listing.status, checked_at=listing.checked_at, data_error=listing.error,
        latest_result=format_filing(company, result, history[company.id]) if result else None) for company, listing, result in triples],
        total=total, page=page, page_size=page_size, coverage=coverage, poll_status=poll_status, catalog_status=catalog_status)


@router.get("/{ticker}", response_model=FilingsPage)
async def company_history(ticker: str, page: int = Query(default=1, ge=1, le=1000),
                          page_size: int = Query(default=20, ge=1, le=100), session=Depends(screening_db)):
    try:
        ticker = normalize_ticker(ticker)
    except ValueError:
        raise HTTPException(422, "Invalid ticker") from None
    company = (await session.execute(select(Company).where(Company.symbol == ticker))).scalar_one_or_none()
    if company is None:
        raise HTTPException(404, "Company not found")
    rows = (await session.execute(select(QuarterlyResult).where(QuarterlyResult.company_id == company.id, QuarterlyResult.provider == PROVIDER)
                                  .order_by(QuarterlyResult.period_end.desc(), QuarterlyResult.id.desc()))).scalars().all()
    return FilingsPage(items=[format_filing(company, row, rows) for row in rows[(page - 1) * page_size:page * page_size]],
                       total=len(rows), page=page, page_size=page_size)
