"""Email intake: professor intake_email + outreach lifecycle fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-26
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # professor's unique inbound intake address
    op.add_column(
        "professors", sa.Column("intake_email", sqlmodel.AutoString(length=320), nullable=True)
    )
    op.create_index(
        "ix_professors_intake_email", "professors", ["intake_email"], unique=True
    )

    # outreach lifecycle + richer email fields
    op.add_column("outreaches", sa.Column("subject", sqlmodel.AutoString(), nullable=True))
    op.add_column("outreaches", sa.Column("body_html", sqlmodel.AutoString(), nullable=True))
    op.add_column(
        "outreaches",
        sa.Column(
            "status",
            sqlmodel.AutoString(length=30),
            nullable=False,
            server_default="pending_triage",
        ),
    )
    op.add_column("outreaches", sa.Column("replied_at", sa.DateTime(), nullable=True))
    op.create_index("ix_outreaches_status", "outreaches", ["status"])


def downgrade() -> None:
    op.drop_index("ix_outreaches_status", table_name="outreaches")
    op.drop_column("outreaches", "replied_at")
    op.drop_column("outreaches", "status")
    op.drop_column("outreaches", "body_html")
    op.drop_column("outreaches", "subject")
    op.drop_index("ix_professors_intake_email", table_name="professors")
    op.drop_column("professors", "intake_email")
