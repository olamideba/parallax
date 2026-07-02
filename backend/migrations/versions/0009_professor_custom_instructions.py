"""Add custom_instructions directive to professors

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-01
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "professors",
        sa.Column("custom_instructions", sqlmodel.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("professors", "custom_instructions")
