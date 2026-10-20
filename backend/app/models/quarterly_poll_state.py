"""Single-row operational heartbeat shared by the worker and API processes."""
from datetime import datetime
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuarterlyPollState(Base):
    __tablename__ = "quarterly_poll_state"

    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    lease_owner: Mapped[str | None] = mapped_column(String(36))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
