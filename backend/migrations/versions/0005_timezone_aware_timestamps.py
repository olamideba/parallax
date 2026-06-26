"""Make outreach/debate timestamps timezone-aware (timestamptz)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_TZ_COLUMNS = [
    ("outreaches", "received_at"),
    ("outreaches", "replied_at"),
    ("debate_traces", "started_at"),
    ("debate_traces", "ended_at"),
]


def upgrade() -> None:
    for table, column in _TZ_COLUMNS:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE timestamptz USING {column} AT TIME ZONE 'UTC'"
        )


def downgrade() -> None:
    for table, column in _TZ_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
        )
