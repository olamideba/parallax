"""Add institution + institution_country to professors

Used by the Assessor as the mobility-lookup destination and as debate context.
Both optional — agents skip destination-specific checks when unset.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-01
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "professors",
        sa.Column("institution", sqlmodel.AutoString(length=255), nullable=True),
    )
    op.add_column(
        "professors",
        sa.Column("institution_country", sqlmodel.AutoString(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("professors", "institution_country")
    op.drop_column("professors", "institution")
