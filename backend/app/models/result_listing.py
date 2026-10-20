"""Exchange catalog membership and durable per-listing Yahoo refresh queue."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResultListing(Base):
    __tablename__ = "result_listings"
    __table_args__ = (Index("ix_result_listing_due", "active", "next_check_at"),)

    company_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    catalog_source: Mapped[str] = mapped_column(String(30))
    exchange_code: Mapped[str] = mapped_column(String(30))
    isin: Mapped[str | None] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    catalog_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    error: Mapped[str | None] = mapped_column(Text)
