# PATH: varex_backend/alembic/versions/0002_align_models.py
"""align models with migration — fix all schema gaps

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── content table ────────────────────────────────────────────
    op.add_column("content", sa.Column("slug",         sa.String(500), nullable=True))
    op.add_column("content", sa.Column("category",     sa.String(100), nullable=True))
    op.add_column("content", sa.Column("is_published", sa.Boolean(),   nullable=False, server_default="false"))
    op.create_index("ix_content_slug",         "content", ["slug"],         unique=True)
    op.create_index("ix_content_access_level", "content", ["access_level"], unique=False)

    # ── team_members table ───────────────────────────────────────
    op.add_column("team_members", sa.Column("avatar_url",          sa.Text(),    nullable=True))
    op.add_column("team_members", sa.Column("github_url",          sa.Text(),    nullable=True))
    op.add_column("team_members", sa.Column("enterprise_projects", postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column("team_members", sa.Column("display_order",       sa.Integer(), nullable=False, server_default="0"))
    op.add_column("team_members", sa.Column("is_active",           sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("team_members", sa.Column("is_published",        sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("team_members", sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=True))

    # ── faqs table — rename published -> is_published ────────────
    op.alter_column("faqs", "published", new_column_name="is_published")

    # ── workshops table ──────────────────────────────────────────
    op.add_column("workshops", sa.Column("trainer_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("workshops", sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"))

    # ── workshop_registrations table ─────────────────────────────
    op.add_column("workshop_registrations", sa.Column("razorpay_payment_id", sa.String(255), nullable=True))
    op.add_column("workshop_registrations", sa.Column("paid",                sa.Boolean(),   nullable=False, server_default="false"))

    # ── projects (portfolio) table ───────────────────────────────
    op.add_column("projects", sa.Column("is_published",     sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("projects", sa.Column("created_by",       postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("projects", sa.Column("diagram_s3_key",   sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("case_study_url",   sa.Text(), nullable=True))
    # Fix JSON vs ARRAY mismatch — tech_stack and outcomes: keep as JSONB
    # (run manually if column already exists as ARRAY):
    # ALTER TABLE projects ALTER COLUMN tech_stack TYPE JSONB USING tech_stack::jsonb;

    # ── certifications table ─────────────────────────────────────
    op.add_column("certifications", sa.Column("expiry_date",    sa.Date(),    nullable=True))
    op.add_column("certifications", sa.Column("is_published",   sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("certifications", sa.Column("team_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("team_members.id"), nullable=True))

    # ── achievements table ───────────────────────────────────────
    op.add_column("achievements", sa.Column("icon_key",     sa.Text(),    nullable=True))
    op.add_column("achievements", sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"))

    # ── consultation_leads table ─────────────────────────────────
    op.add_column("consultation_leads", sa.Column("is_free_consult", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("consultation_leads", sa.Column("updated_at",      sa.DateTime(timezone=True), nullable=True))

    # ── subscriptions table ──────────────────────────────────────
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)

    # ── users table ──────────────────────────────────────────────
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Reverse all changes (abbreviated)
    op.drop_column("content", "slug")
    op.drop_column("content", "category")
    op.drop_column("content", "is_published")
    # ... (add full reversal if needed)
