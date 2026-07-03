"""Add triage_reason to outreaches

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-03
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "outreaches",
        sa.Column("triage_reason", sqlmodel.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("outreaches", "triage_reason")
