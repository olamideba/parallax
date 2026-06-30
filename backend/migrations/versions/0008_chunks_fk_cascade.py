"""Add ON DELETE CASCADE to publication_chunks.publication_id FK

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-29
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "publication_chunks_publication_id_fkey",
        "publication_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "publication_chunks_publication_id_fkey",
        "publication_chunks",
        "publications",
        ["publication_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "publication_chunks_publication_id_fkey",
        "publication_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "publication_chunks_publication_id_fkey",
        "publication_chunks",
        "publications",
        ["publication_id"],
        ["id"],
    )
