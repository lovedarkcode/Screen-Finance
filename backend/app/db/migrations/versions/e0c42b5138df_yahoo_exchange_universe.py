"""Exchange catalogs, Yahoo refresh queue and explicit financial provenance.

Revision ID: e0c42b5138df
Revises: d9b31a4027ce
"""
from alembic import op
import sqlalchemy as sa

revision = "e0c42b5138df"
down_revision = "d9b31a4027ce"
branch_labels = depends_on = None


def upgrade():
    op.add_column("quarterly_results", sa.Column("provider", sa.String(30), nullable=False, server_default="Financial Modeling Prep"))
    op.add_column("quarterly_results", sa.Column("period_basis", sa.String(40), nullable=False, server_default="reported"))
    op.drop_constraint("uq_quarterly_result_company_period", "quarterly_results", type_="unique")
    op.create_unique_constraint("uq_quarterly_result_company_period", "quarterly_results", ["company_id", "provider", "fiscal_year", "quarter_period"])
    op.create_table("result_listings",
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("stocks.id"), primary_key=True),
        sa.Column("catalog_source", sa.String(30), nullable=False),
        sa.Column("exchange_code", sa.String(30), nullable=False),
        sa.Column("isin", sa.String(20)), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("catalog_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True)), sa.Column("next_check_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"), sa.Column("error", sa.Text()))
    op.create_index("ix_result_listing_due", "result_listings", ["active", "next_check_at"])


def downgrade():
    # A downgrade must never collapse independently sourced quarters silently.
    op.drop_table("result_listings")
    op.drop_constraint("uq_quarterly_result_company_period", "quarterly_results", type_="unique")
    op.create_unique_constraint("uq_quarterly_result_company_period", "quarterly_results", ["company_id", "fiscal_year", "quarter_period"])
    op.drop_column("quarterly_results", "period_basis")
    op.drop_column("quarterly_results", "provider")
