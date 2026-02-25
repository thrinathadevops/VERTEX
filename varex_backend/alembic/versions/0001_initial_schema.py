"""Initial schema — all VAREX tables

Revision ID: 0001
Revises:
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── users ──────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name",            sa.String(120),  nullable=False),
        sa.Column("email",           sa.String(255),  nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255),  nullable=False),
        sa.Column("role",            sa.String(20),   nullable=False, server_default="free_user"),
        sa.Column("company",         sa.String(120),  nullable=True),
        sa.Column("is_active",       sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── subscriptions ──────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id",                   postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",              postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_type",            sa.String(20),  nullable=False, server_default="free"),
        sa.Column("status",               sa.String(20),  nullable=False, server_default="active"),
        sa.Column("price_paid",           sa.Float(),     nullable=True),
        sa.Column("start_date",           sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expiry_date",          sa.DateTime(timezone=True), nullable=True),
        sa.Column("razorpay_order_id",    sa.String(120), nullable=True),
        sa.Column("razorpay_payment_id",  sa.String(120), nullable=True),
    )

    # ── content ────────────────────────────────────────────────
    op.create_table(
        "content",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title",        sa.String(255),  nullable=False),
        sa.Column("slug",         sa.String(255),  nullable=False, unique=True),
        sa.Column("body",         sa.Text(),       nullable=False),
        sa.Column("access_level", sa.String(20),   nullable=False, server_default="free"),
        sa.Column("category",     sa.String(50),   nullable=True),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_content_slug", "content", ["slug"], unique=True)

    # ── projects (portfolio) ───────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title",           sa.String(255), nullable=False),
        sa.Column("slug",            sa.String(255), nullable=False, unique=True),
        sa.Column("category",        sa.String(50),  nullable=False),
        sa.Column("summary",         sa.String(500), nullable=False),
        sa.Column("description",     sa.Text(),      nullable=True),
        sa.Column("tech_stack",      postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("outcomes",        postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("diagram_s3_key",  sa.String(255), nullable=True),
        sa.Column("github_url",      sa.String(500), nullable=True),
        sa.Column("case_study_url",  sa.String(500), nullable=True),
        sa.Column("is_featured",     sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)

    # ── team_members ───────────────────────────────────────────
    op.create_table(
        "team_members",
        sa.Column("id",                postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name",              sa.String(120), nullable=False),
        sa.Column("slug",              sa.String(120), nullable=False, unique=True),
        sa.Column("title",             sa.String(120), nullable=False),
        sa.Column("bio",               sa.Text(),      nullable=True),
        sa.Column("years_experience",  sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("specializations",   postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("tools",             postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("pricing",           postgresql.JSONB(), nullable=True),
        sa.Column("available_for",     postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("available_from",    sa.DateTime(timezone=True), nullable=True),
        sa.Column("avatar_s3_key",     sa.String(255), nullable=True),
        sa.Column("linkedin_url",      sa.String(500), nullable=True),
    )

    # ── certifications ─────────────────────────────────────────
    op.create_table(
        "certifications",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title",          sa.String(255), nullable=False),
        sa.Column("issuing_body",   sa.String(120), nullable=False),
        sa.Column("domain",         sa.String(50),  nullable=False),
        sa.Column("credential_url", sa.String(500), nullable=True),
        sa.Column("issued_date",    sa.DateTime(timezone=True), nullable=True),
        sa.Column("badge_s3_key",   sa.String(255), nullable=True),
    )

    # ── achievements ───────────────────────────────────────────
    op.create_table(
        "achievements",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title",       sa.String(255), nullable=False),
        sa.Column("description", sa.Text(),      nullable=False),
        sa.Column("metric",      sa.String(100), nullable=True),
        sa.Column("year",        sa.String(10),  nullable=True),
    )

    # ── faqs ───────────────────────────────────────────────────
    op.create_table(
        "faqs",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question",   sa.Text(),     nullable=False),
        sa.Column("answer",     sa.Text(),     nullable=False),
        sa.Column("category",   sa.String(50), nullable=False),
        sa.Column("order_rank", sa.Integer(),  nullable=False, server_default="0"),
        sa.Column("published",  sa.Boolean(),  nullable=False, server_default="true"),
    )

    # ── workshops ──────────────────────────────────────────────
    op.create_table(
        "workshops",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title",          sa.String(255), nullable=False),
        sa.Column("slug",           sa.String(255), nullable=False, unique=True),
        sa.Column("description",    sa.Text(),      nullable=True),
        sa.Column("curriculum",     sa.Text(),      nullable=True),
        sa.Column("mode",           sa.String(20),  nullable=False, server_default="online"),
        sa.Column("status",         sa.String(20),  nullable=False, server_default="upcoming"),
        sa.Column("price_inr",      sa.Float(),     nullable=True),
        sa.Column("duration_hours", sa.Integer(),   nullable=False, server_default="2"),
        sa.Column("max_seats",      sa.Integer(),   nullable=False, server_default="30"),
        sa.Column("seats_booked",   sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workshops_slug", "workshops", ["slug"], unique=True)

    # ── workshop_registrations ─────────────────────────────────
    op.create_table(
        "workshop_registrations",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workshop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id",     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id",     ondelete="CASCADE"), nullable=False),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("workshop_id", "user_id", name="uq_workshop_user"),
    )

    # ── consultation_leads ─────────────────────────────────────
    op.create_table(
        "consultation_leads",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name",             sa.String(120), nullable=False),
        sa.Column("email",            sa.String(255), nullable=False),
        sa.Column("phone",            sa.String(20),  nullable=True),
        sa.Column("company",          sa.String(120), nullable=True),
        sa.Column("service_interest", sa.String(100), nullable=False),
        sa.Column("message",          sa.Text(),      nullable=True),
        sa.Column("preferred_slot",   sa.String(100), nullable=True),
        sa.Column("status",           sa.String(30),  nullable=False, server_default="new"),
        sa.Column("utm_source",       sa.String(100), nullable=True),
        sa.Column("utm_medium",       sa.String(100), nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("consultation_leads")
    op.drop_table("workshop_registrations")
    op.drop_table("workshops")
    op.drop_table("faqs")
    op.drop_table("achievements")
    op.drop_table("certifications")
    op.drop_table("team_members")
    op.drop_table("projects")
    op.drop_index("ix_content_slug",  table_name="content")
    op.drop_table("content")
    op.drop_table("subscriptions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
