"""Validate provider records before they enter the financial database."""
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

Money = Annotated[Decimal, Field(allow_inf_nan=False, max_digits=38, decimal_places=10)]


def normalize_ticker(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.&^-]{0,19}", value):
        raise ValueError("Invalid ticker")
    return value


class IncomeStatement(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    symbol: str
    provider: str = "Financial Modeling Prep"
    period_basis: str = "reported"
    fiscal_year: int = Field(validation_alias=AliasChoices("fiscalYear", "calendarYear", "fiscal_year"), ge=1900, le=2200)
    quarter_period: Literal["Q1", "Q2", "Q3", "Q4"] = Field(alias="period")
    period_end: date = Field(alias="date")
    filing_date: date | None = Field(default=None, validation_alias=AliasChoices("filingDate", "fillingDate", "filing_date"))
    currency: str = Field(alias="reportedCurrency", pattern=r"^[A-Z]{3}$")
    revenue: Money | None = None
    net_income: Money | None = Field(default=None, alias="netIncome")
    operating_income: Money | None = Field(default=None, alias="operatingIncome")
    basic_eps: Money | None = Field(default=None, alias="eps")
    diluted_eps: Money | None = Field(default=None, alias="epsDiluted")

    @field_validator("symbol")
    @classmethod
    def ticker(cls, value):
        return normalize_ticker(value)

    @field_validator("revenue", "net_income", "operating_income", "basic_eps", "diluted_eps", mode="before")
    @classmethod
    def not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("A boolean is not a financial figure")
        return value

    @field_validator("filing_date", mode="before")
    @classmethod
    def absent_filing_date(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def check_dates_and_figures(self):
        today = datetime.now(UTC).date()
        if self.period_end > today or self.filing_date and self.filing_date > today:
            raise ValueError("Future report or filing date")
        if self.filing_date and self.filing_date < self.period_end:
            raise ValueError("Filing predates the reporting period")
        if self.revenue is None and self.net_income is None:
            raise ValueError("Income statement has no usable financial figures")
        return self

    def financial_values(self):
        diluted = self.diluted_eps is not None
        margin = self.operating_income / self.revenue * 100 if self.operating_income is not None and self.revenue is not None and self.revenue > 0 else None
        return {
            "provider": self.provider, "period_basis": self.period_basis,
            "fiscal_year": self.fiscal_year, "quarter_period": self.quarter_period,
            "period_end": self.period_end, "filing_date": self.filing_date, "currency": self.currency,
            "revenue": self.revenue, "net_income": self.net_income,
            "eps": self.diluted_eps if diluted else self.basic_eps,
            "eps_basis": "diluted" if diluted else "basic" if self.basic_eps is not None else None,
            "operating_margin": margin.quantize(Decimal("0.0000000001")) if margin is not None else None,
        }


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    symbol: str
    name: str = Field(alias="companyName", min_length=1, max_length=255)
    exchange: str = Field(validation_alias=AliasChoices("exchangeShortName", "exchange"), min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=10)
    sector: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @field_validator("symbol")
    @classmethod
    def ticker(cls, value):
        return normalize_ticker(value)
