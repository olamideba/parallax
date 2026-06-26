"""Pull display_name from raw_user_meta_data in auth trigger

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO public.professors (id, email, display_name)
            VALUES (
                NEW.id,
                NEW.email,
                NEW.raw_user_meta_data->>'display_name'
            )
            ON CONFLICT (id) DO NOTHING;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
    )


def downgrade() -> None:
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
