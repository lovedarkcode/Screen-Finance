"""Strict, non-executable natural-language screen definitions."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

Period = Literal["annual", "ttm", "quarterly", "snapshot"]
Operator = Literal["gt", "gte", "lt", "lte", "eq", "between"]
Exchange = Literal["NSE", "BSE", "NASDAQ", "NYSE", "NYSE American", "NYSE Arca", "Cboe", "OTC", "OTCQB", "OTCQX"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FinancialFilter(StrictModel):
    field: str = Field(min_length=1, max_length=40)
    operator: Operator
    value: FiniteFloat | tuple[FiniteFloat, FiniteFloat]
    period: Period | None = None
    period_end: date | None = Field(default=None, description="Exact fiscal end only when explicitly requested; null means latest available reporting period, never today's date.")
    currency: Literal["USD", "INR"] | None = None

    @field_validator("value", mode="before")
    @classmethod
    def numeric_values(cls, value):
        values = value if isinstance(value, (list, tuple)) else [value]
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in values):
            raise ValueError("Thresholds must be JSON numbers")
        return value


class ScreenDefinition(StrictModel):
    market: Literal["IN", "US"] | None = None
    as_of: date | None = Field(default=None, description="Only use data observed by this date; null means current available data.")
    exchange: Exchange | None = None
    exchanges: list[Exchange] = Field(default_factory=list, max_length=10, description="Any of these exchanges; use for NSE or BSE, NASDAQ or NYSE. Financial filters still all apply.")
    sector: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    filters: list[FinancialFilter] = Field(default_factory=list, max_length=12)
    sort_by: str = Field(default="market_cap", max_length=40)
    sort_period: Period | None = None
    sort_desc: bool = True
    limit: int = Field(default=25, ge=1, le=100)


class RawFilter(FinancialFilter):
    source_text: str = Field(min_length=1, max_length=1000)


class ParsedScreen(ScreenDefinition):
    filters: list[RawFilter] = Field(default_factory=list, max_length=12)
    unresolved_conditions: list[str] = Field(default_factory=list, max_length=12)


class SearchRequest(StrictModel):
    query: str = Field(min_length=3, max_length=1500)
    page: int = Field(default=1, ge=1, le=1000)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter a financial screening request")
        return value


class ExecuteRequest(StrictModel):
    screen: ScreenDefinition
    page: int = Field(default=1, ge=1, le=1000)
    original_query: str | None = Field(default=None, max_length=1500, description="Optional source prompt for edited screens; context only, never reparsed.")


class ScreenResponse(StrictModel):
    original_query: str | None = None
    status: Literal["success", "clarification", "unsupported", "invalid"]
    parsed_filters: ScreenDefinition | None = None
    stocks: list[dict] = Field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 25
    data_as_of: str | None = None
    universe_count: int = Field(default=0, description="All imported stocks in the selected market (or all markets), before other filters and pagination, including stocks without financials.")
    empty_reason: Literal["empty_universe", "no_matches", "missing_metrics", "unavailable_period", "incompatible_currency", "page_out_of_range"] | None = None
    explanation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    clarification: str | None = None
    cached: bool = False
    execution_ms: float = 0
