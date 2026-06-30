"""Resize publication_chunks.embedding from 1536 to 1024 dims

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-28
"""
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The publication ingestion feature is not yet live, so the column is empty;
    # a straight type change is safe. (A populated column would need re-embedding.)
    op.alter_column(
        "publication_chunks",
        "embedding",
        type_=Vector(1024),
        existing_type=Vector(1536),
        existing_nullable=True,
        postgresql_using="embedding::vector(1024)",
    )


def downgrade() -> None:
    op.alter_column(
        "publication_chunks",
        "embedding",
        type_=Vector(1536),
        existing_type=Vector(1024),
        existing_nullable=True,
        postgresql_using="embedding::vector(1536)",
    )
