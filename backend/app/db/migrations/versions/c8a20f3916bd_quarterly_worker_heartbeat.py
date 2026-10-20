"""Persist the quarterly worker heartbeat without requiring Redis.

Revision ID: c8a20f3916bd
Revises: b7d91e2084ac
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c8a20f3916bd"
down_revision = "b7d91e2084ac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("quarterly_poll_state", sa.Column("name", sa.String(40), primary_key=True),
                    sa.Column("payload", postgresql.JSONB(), nullable=False))


def downgrade():
    op.drop_table("quarterly_poll_state")
