"""Bounded PostgreSQL worker lease without holding idle transactions during API calls."""
from alembic import op
import sqlalchemy as sa

revision = "d9b31a4027ce"
down_revision = "c8a20f3916bd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("quarterly_poll_state", sa.Column("lease_owner", sa.String(36)))
    op.add_column("quarterly_poll_state", sa.Column("lease_until", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_column("quarterly_poll_state", "lease_until")
    op.drop_column("quarterly_poll_state", "lease_owner")
