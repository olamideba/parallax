"""Add provider_message_id to outreaches for inbound-webhook idempotency

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-04
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "outreaches",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_outreaches_provider_message_id",
        "outreaches",
        ["provider_message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outreaches_provider_message_id", table_name="outreaches")
    op.drop_column("outreaches", "provider_message_id")
