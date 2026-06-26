"""Initial schema with Supabase auth trigger

Revision ID: 0001
Revises:
Create Date: 2026-06-26
"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # professors — id is set from auth.users.id, never generated here
    op.create_table(
        "professors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("display_name", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("open_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("students_committed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("budget_context", sqlmodel.AutoString(), nullable=True),
        sa.Column("recruiting_topics", sqlmodel.AutoString(), nullable=False, server_default="[]"),
        sa.Column(
            "gatekeeper_aggressiveness", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_professors_id", "professors", ["id"])
    op.create_index("ix_professors_email", "professors", ["email"], unique=True)

    # FK to auth.users (Supabase-managed schema — raw SQL, not tracked by SQLAlchemy)
    op.execute(
        """
        ALTER TABLE professors
        ADD CONSTRAINT professors_id_fkey
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE
        """
    )

    # Auto-create a professors row when Supabase creates an auth user
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO public.professors (id, email)
            VALUES (NEW.id, NEW.email)
            ON CONFLICT (id) DO NOTHING;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
        """
    )
    op.execute(
        """
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
        """
    )

    op.create_table(
        "publications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("title", sqlmodel.AutoString(), nullable=True),
        sa.Column("doi", sqlmodel.AutoString(), nullable=True),
        sa.Column("url", sqlmodel.AutoString(), nullable=True),
        sa.Column("storage_key", sqlmodel.AutoString(), nullable=True),
        sa.Column("indexed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publications_id", "publications", ["id"])
    op.create_index("ix_publications_professor_id", "publications", ["professor_id"])

    op.create_table(
        "publication_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("publication_id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("chunk_text", sqlmodel.AutoString(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.id"]),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publication_chunks_id", "publication_chunks", ["id"])
    op.create_index(
        "ix_publication_chunks_publication_id", "publication_chunks", ["publication_id"]
    )
    op.create_index(
        "ix_publication_chunks_professor_id", "publication_chunks", ["professor_id"]
    )

    op.create_table(
        "outreaches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column(
            "channel", sqlmodel.AutoString(length=50), nullable=False, server_default="email"
        ),
        sa.Column("sender_email", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("sender_name", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("body", sqlmodel.AutoString(), nullable=False),
        sa.Column(
            "attachment_keys", sqlmodel.AutoString(), nullable=False, server_default="[]"
        ),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("triage_verdict", sqlmodel.AutoString(length=20), nullable=True),
        sa.Column("debate_trace_id", sa.UUID(), nullable=True),
        sa.Column("decision_label", sqlmodel.AutoString(length=30), nullable=True),
        sa.Column("decision_rationale", sqlmodel.AutoString(), nullable=True),
        sa.Column("drafted_reply", sqlmodel.AutoString(), nullable=True),
        sa.Column(
            "overridden_by_professor", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("extracted_profile_json", sqlmodel.AutoString(), nullable=True),
        sa.Column("extracted_claims_json", sqlmodel.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outreaches_id", "outreaches", ["id"])
    op.create_index("ix_outreaches_professor_id", "outreaches", ["professor_id"])
    op.create_index("ix_outreaches_sender_email", "outreaches", ["sender_email"])
    op.create_index("ix_outreaches_debate_trace_id", "outreaches", ["debate_trace_id"])

    op.create_table(
        "debate_traces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("outreach_id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("round_cap", sa.Integer(), nullable=False),
        sa.Column("terminated_at_round", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("turns_json", sqlmodel.AutoString(), nullable=False, server_default="[]"),
        sa.ForeignKeyConstraint(["outreach_id"], ["outreaches.id"]),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debate_traces_id", "debate_traces", ["id"])
    op.create_index("ix_debate_traces_outreach_id", "debate_traces", ["outreach_id"])
    op.create_index("ix_debate_traces_professor_id", "debate_traces", ["professor_id"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user()")
    op.drop_table("debate_traces")
    op.drop_table("outreaches")
    op.drop_table("publication_chunks")
    op.drop_table("publications")
    op.drop_table("professors")
    op.execute("DROP EXTENSION IF EXISTS vector")
