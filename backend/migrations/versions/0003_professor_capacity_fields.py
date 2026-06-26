"""Expand professor capacity fields and add triage preferences

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("professors", "budget_context")
    op.add_column("professors", sa.Column("budget_amount", sa.Integer(), nullable=True))
    op.add_column("professors", sa.Column("funding_source", sqlmodel.AutoString(), nullable=True))
    op.add_column(
        "professors",
        sa.Column("auto_resolve_declines", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "professors",
        sa.Column("hold_when_at_capacity", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("professors", "hold_when_at_capacity")
    op.drop_column("professors", "auto_resolve_declines")
    op.drop_column("professors", "funding_source")
    op.drop_column("professors", "budget_amount")
    op.add_column("professors", sa.Column("budget_context", sqlmodel.AutoString(), nullable=True))
