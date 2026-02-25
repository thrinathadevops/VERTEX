# PATH: varex_backend/alembic/versions/0003_add_indexes.py
"""add missing database indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-25
"""
from alembic import op

revision    = "0003"
down_revision = "0002"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # FIX 7.4 — subscriptions.user_id full-table-scan on every auth check
    op.create_index("ix_subscriptions_user_id",  "subscriptions",  ["user_id"],     unique=False)

    # FIX 7.5 — content.access_level full-table-scan on every premium filter
    op.create_index("ix_content_access_level",   "content",        ["access_level"], unique=False)

    # Bonus indexes for common lookups
    op.create_index("ix_users_email",            "users",          ["email"],        unique=True)
    op.create_index("ix_users_role",             "users",          ["role"],         unique=False)
    op.create_index("ix_workshops_status",       "workshops",      ["status"],       unique=False)
    op.create_index("ix_leads_status",           "consultation_leads", ["status"],   unique=False)
    op.create_index("ix_content_is_published",   "content",        ["is_published"], unique=False)
    op.create_index("ix_team_display_order",     "team_members",   ["display_order"],unique=False)


def downgrade() -> None:
    op.drop_index("ix_subscriptions_user_id",  table_name="subscriptions")
    op.drop_index("ix_content_access_level",   table_name="content")
    op.drop_index("ix_users_email",            table_name="users")
    op.drop_index("ix_users_role",             table_name="users")
    op.drop_index("ix_workshops_status",       table_name="workshops")
    op.drop_index("ix_leads_status",           table_name="consultation_leads")
    op.drop_index("ix_content_is_published",   table_name="content")
    op.drop_index("ix_team_display_order",     table_name="team_members")
