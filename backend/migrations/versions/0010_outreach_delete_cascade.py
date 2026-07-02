"""Add ON DELETE CASCADE to debate_traces.outreach_id FK

Lets the professor delete an outreach (e.g. a stub/test row) without first
hand-deleting its debate trace.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-01
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "debate_traces_outreach_id_fkey",
        "debate_traces",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "debate_traces_outreach_id_fkey",
        "debate_traces",
        "outreaches",
        ["outreach_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "debate_traces_outreach_id_fkey",
        "debate_traces",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "debate_traces_outreach_id_fkey",
        "debate_traces",
        "outreaches",
        ["outreach_id"],
        ["id"],
    )
