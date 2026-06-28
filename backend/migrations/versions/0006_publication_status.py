"""Add ingestion lifecycle status to publications

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-28
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "publications",
        sa.Column(
            "status",
            sqlmodel.AutoString(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_index("ix_publications_status", "publications", ["status"])
    # Backfill: anything already indexed is in the terminal indexed state.
    op.execute("UPDATE publications SET status = 'indexed' WHERE indexed = true")


def downgrade() -> None:
    op.drop_index("ix_publications_status", table_name="publications")
    op.drop_column("publications", "status")
