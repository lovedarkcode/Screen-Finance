"""Add validated screening metrics to existing stock/financial tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a31f70d293c1"
down_revision = "f6fe622759e5"
branch_labels = None
depends_on = None
METRICS = ["roe", "pe", "operating_margin", "net_profit_margin", "revenue_growth", "debt_to_equity", "current_ratio", "total_debt", "net_debt", "operating_cash_flow", "free_cash_flow", "free_cash_flow_margin"]


def upgrade():
    op.add_column("stocks", sa.Column("currency", sa.String(3), nullable=True))
    op.add_column("stocks", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_stocks_updated_at", "stocks", ["updated_at"])
    op.create_index("ix_stocks_market_sector", "stocks", ["country", "sector"])
    for column in [sa.Column("snapshot_key", sa.String(32)), sa.Column("period_end", sa.Date), sa.Column("currency", sa.String(3)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.Column("validation_version", sa.Integer), sa.Column("provenance", postgresql.JSONB)]:
        op.add_column("financials", column)
    for name in METRICS:
        op.add_column("financials", sa.Column(name, sa.Float, nullable=True))
        op.create_index(f"ix_financials_{name}", "financials", [name])
    op.create_unique_constraint("uq_financial_snapshot", "financials", ["stock_id", "snapshot_key"])
    op.create_index("ix_financial_latest", "financials", ["stock_id", "period_type", "period_end", "updated_at"])
    op.create_index("ix_financials_updated_at", "financials", ["updated_at"])


def downgrade():
    op.drop_index("ix_financials_updated_at", "financials")
    op.drop_index("ix_financial_latest", "financials")
    op.drop_constraint("uq_financial_snapshot", "financials", type_="unique")
    for name in reversed(METRICS):
        op.drop_index(f"ix_financials_{name}", "financials")
        op.drop_column("financials", name)
    for name in ["provenance", "validation_version", "updated_at", "currency", "period_end", "snapshot_key"]:
        op.drop_column("financials", name)
    op.drop_index("ix_stocks_market_sector", "stocks")
    op.drop_index("ix_stocks_updated_at", "stocks")
    op.drop_column("stocks", "updated_at")
    op.drop_column("stocks", "currency")
