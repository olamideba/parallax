"""Add created_at/updated_at to all tables, backfilling from the closest
existing timestamp where one exists

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-04
"""
import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

_NOW = sa.text("now()")

# Tables with no prior timestamp to backfill from — server_default populates
# existing rows with the migration's execution time.
_NO_PRIOR_TIMESTAMP = ("professors", "publications", "publication_chunks")


def upgrade() -> None:
    for table in _NO_PRIOR_TIMESTAMP:
        op.add_column(
            table, sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False)
        )
        op.add_column(
            table, sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False)
        )

    # outreaches — backfill from received_at / replied_at so historical rows
    # keep a meaningful value instead of collapsing to "now".
    op.add_column(
        "outreaches", sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=True)
    )
    op.add_column(
        "outreaches", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=True)
    )
    op.execute(
        "UPDATE outreaches SET created_at = received_at, "
        "updated_at = COALESCE(replied_at, received_at)"
    )
    op.alter_column("outreaches", "created_at", nullable=False)
    op.alter_column("outreaches", "updated_at", nullable=False)

    # debate_traces — backfill from started_at / ended_at.
    op.add_column(
        "debate_traces", sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=True)
    )
    op.add_column(
        "debate_traces", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=True)
    )
    op.execute(
        "UPDATE debate_traces SET created_at = started_at, "
        "updated_at = COALESCE(ended_at, started_at)"
    )
    op.alter_column("debate_traces", "created_at", nullable=False)
    op.alter_column("debate_traces", "updated_at", nullable=False)


def downgrade() -> None:
    for table in (*_NO_PRIOR_TIMESTAMP, "outreaches", "debate_traces"):
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
