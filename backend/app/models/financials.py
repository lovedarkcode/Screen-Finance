"""Financial statements ORM model (quarterly/annual)."""
from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Financials(Base):
    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint("stock_id", "snapshot_key", name="uq_financial_snapshot"),
        Index("ix_financial_latest", "stock_id", "period_type", "period_end", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    period_type: Mapped[str] = mapped_column(String(10))
    sales: Mapped[float | None] = mapped_column(Float, nullable=True)
    expenses: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    validation_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    roe: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    pe: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    operating_margin: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    net_profit_margin: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    revenue_growth: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    debt_to_equity: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    current_ratio: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    total_debt: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    net_debt: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    operating_cash_flow: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    free_cash_flow: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    free_cash_flow_margin: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
