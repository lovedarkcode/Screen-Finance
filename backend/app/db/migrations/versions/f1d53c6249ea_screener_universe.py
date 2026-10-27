"""Independent financial refresh queue for the exchange-wide screener."""
from alembic import op
import sqlalchemy as sa

revision = "f1d53c6249ea"
down_revision = "e0c42b5138df"
branch_labels = depends_on = None


def upgrade():
    op.add_column("result_listings", sa.Column("screener_checked_at", sa.DateTime(timezone=True)))
    op.add_column("result_listings", sa.Column("screener_next_check_at", sa.DateTime(timezone=True)))
    op.add_column("result_listings", sa.Column("screener_error", sa.String(100)))
    op.create_index("ix_result_listing_screener_due", "result_listings", ["active", "screener_next_check_at"])


def downgrade():
    op.drop_index("ix_result_listing_screener_due", table_name="result_listings")
    for column in ("screener_error", "screener_next_check_at", "screener_checked_at"):
        op.drop_column("result_listings", column)
