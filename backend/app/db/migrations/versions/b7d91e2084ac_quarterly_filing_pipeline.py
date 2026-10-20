"""Quarterly provider filings and durable summary queue; reuse the company master.

Revision ID: b7d91e2084ac
Revises: a31f70d293c1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b7d91e2084ac"
down_revision = "a31f70d293c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quarterly_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("quarter_period", sa.String(2), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("filing_date", sa.Date()),
        sa.Column("filing_date_kind", sa.String(24), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        *[sa.Column(field, sa.Numeric(38, 10)) for field in ("revenue", "net_income", "eps", "operating_margin")],
        sa.Column("eps_basis", sa.String(10)),
        sa.Column("raw_json_dump", postgresql.JSONB(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("ai_summary_json", postgresql.JSONB()),
        sa.Column("summary_model", sa.String(150)),
        sa.Column("summary_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("summary_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_error", sa.String(80)),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("summary_lease_until", sa.DateTime(timezone=True)),
        sa.Column("summary_token", sa.String(36)),
        sa.UniqueConstraint("company_id", "fiscal_year", "quarter_period", name="uq_quarterly_result_company_period"),
        sa.CheckConstraint("quarter_period IN ('Q1','Q2','Q3','Q4')", name="ck_quarterly_result_period"),
        sa.CheckConstraint("fiscal_year BETWEEN 1900 AND 2200", name="ck_quarterly_result_year"),
        sa.CheckConstraint("summary_status IN ('pending','processing','completed','failed')", name="ck_quarterly_result_summary_status"),
    )
    op.create_index("ix_quarterly_result_latest", "quarterly_results", ["filing_date", "period_end", "id"])
    op.create_index("ix_quarterly_result_company_history", "quarterly_results", ["company_id", "period_end"])
    op.create_index("ix_quarterly_result_summary_queue", "quarterly_results", ["summary_status", "next_retry_at"])


def downgrade():
    op.drop_table("quarterly_results")
