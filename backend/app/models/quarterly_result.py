"""Durable provider filings and recoverable AI-summary work."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuarterlyResult(Base):
    __tablename__ = "quarterly_results"
    __table_args__ = (
        UniqueConstraint("company_id", "provider", "fiscal_year", "quarter_period", name="uq_quarterly_result_company_period"),
        CheckConstraint("quarter_period IN ('Q1','Q2','Q3','Q4')", name="ck_quarterly_result_period"),
        CheckConstraint("fiscal_year BETWEEN 1900 AND 2200", name="ck_quarterly_result_year"),
        CheckConstraint("summary_status IN ('pending','processing','completed','failed')", name="ck_quarterly_result_summary_status"),
        Index("ix_quarterly_result_latest", "filing_date", "period_end", "id"),
        Index("ix_quarterly_result_company_history", "company_id", "period_end"),
        Index("ix_quarterly_result_summary_queue", "summary_status", "next_retry_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    provider: Mapped[str] = mapped_column(String(30), default="Financial Modeling Prep", server_default="Financial Modeling Prep")
    period_basis: Mapped[str] = mapped_column(String(40), default="reported", server_default="reported")
    fiscal_year: Mapped[int] = mapped_column(Integer)
    quarter_period: Mapped[str] = mapped_column(String(2))
    period_end: Mapped[date] = mapped_column(Date)
    filing_date: Mapped[date | None] = mapped_column(Date)
    filing_date_kind: Mapped[str] = mapped_column(String(24))
    currency: Mapped[str] = mapped_column(String(3))
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(38, 10))
    net_income: Mapped[Decimal | None] = mapped_column(Numeric(38, 10))
    eps: Mapped[Decimal | None] = mapped_column(Numeric(38, 10))
    eps_basis: Mapped[str | None] = mapped_column(String(10))
    operating_margin: Mapped[Decimal | None] = mapped_column(Numeric(38, 10))
    raw_json_dump: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    source_hash: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_summary_json: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    summary_model: Mapped[str | None] = mapped_column(String(150))
    summary_status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    summary_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    summary_error: Mapped[str | None] = mapped_column(String(80))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_token: Mapped[str | None] = mapped_column(String(36))
