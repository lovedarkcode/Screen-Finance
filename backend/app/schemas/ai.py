"""AI / RAG Pydantic schemas."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


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


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = Field(min_length=1, max_length=40)


class ResearchClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=10, max_length=700)
    evidenceIds: list[str] = Field(min_length=1, max_length=8)
    findingId: str
    significance: Literal["high", "medium", "low"]


class ResearchDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: list[ResearchClaim] = Field(min_length=1, max_length=3)
    strengths: list[ResearchClaim] = Field(max_length=5)
    risks: list[ResearchClaim] = Field(max_length=5)
    watchItems: list[ResearchClaim] = Field(max_length=4)


class ResearchSelection(BaseModel):
    """NVIDIA ranks verified findings; financial assertions are server-controlled."""
    model_config = ConfigDict(extra="forbid")
    summary: list[str] = Field(min_length=1, max_length=3)
    strengths: list[str] = Field(max_length=5)
    risks: list[str] = Field(max_length=5)
    watchItems: list[str] = Field(max_length=4)


class AnalysisSource(BaseModel):
    id: str
    label: str
    url: str
    retrievedAt: datetime


class AnalysisEvidence(BaseModel):
    id: str
    label: str
    value: FiniteFloat | str
    unit: Literal["currency", "percent", "times", "number", "text"]
    currency: str | None = None
    period: str
    sourceId: str
    formula: str | None = None
    inputs: list[str] = Field(default_factory=list)
    kind: Literal["provider", "normalized", "calculated"] = "provider"
    periodType: Literal["quote", "snapshot", "annual", "quarterly", "instant", "ttm", "comparison"] = "snapshot"
    periodEnd: date | None = None
    operation: str | None = None
    sourceField: str | None = None
    symbol: str = ""
    exchange: str = ""


class EvidenceIssue(BaseModel):
    code: str
    severity: Literal["high", "medium", "low"]
    text: str
    evidenceIds: list[str] = Field(default_factory=list)


class EvidenceQuality(BaseModel):
    coverage: Literal["limited", "partial", "available"]
    checkedCalculations: int
    providerMetrics: int
    annualPeriods: int
    quarterlyPeriods: int
    issues: list[EvidenceIssue]


class FinancialTrend(BaseModel):
    period: str
    periodEnd: date
    periodType: Literal["annual", "quarterly"]
    revenueId: str | None = None
    netIncomeId: str | None = None
    netMarginId: str | None = None


class StockAnalysisReport(BaseModel):
    companyId: str
    analysisRunId: str
    symbol: str
    companyName: str
    exchange: str
    currency: str
    financialCurrency: str | None
    generatedAt: datetime
    quoteAsOf: str | None
    provider: Literal["NVIDIA", "Nebius"] = "NVIDIA"
    model: str
    cached: bool = False
    research: ResearchDraft
    metricIds: list[str]
    evidence: list[AnalysisEvidence]
    sources: list[AnalysisSource]
    warnings: list[str]
    quality: EvidenceQuality
    trends: list[FinancialTrend] = Field(default_factory=list)
