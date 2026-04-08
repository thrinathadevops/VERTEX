"""expand portfolio projects for case study structure

Revision ID: a4e2b1d9f6c3
Revises: 9d5b7d3c4e21
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a4e2b1d9f6c3"
down_revision = "9d5b7d3c4e21"
branch_labels = None
depends_on = None


project_type_enum = postgresql.ENUM(
    "client_work",
    "personal_project",
    "internal_product",
    "case_study",
    name="projecttype",
)


def upgrade() -> None:
    bind = op.get_bind()
    project_type_enum.create(bind, checkfirst=True)

    op.add_column("projects", sa.Column("project_type", project_type_enum, nullable=True))
    op.add_column("projects", sa.Column("hero_image_url", sa.String(length=512), nullable=True))
    op.add_column("projects", sa.Column("screenshots", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("projects", sa.Column("demo_url", sa.String(length=512), nullable=True))
    op.add_column("projects", sa.Column("duration", sa.String(length=120), nullable=True))
    op.add_column("projects", sa.Column("team_size", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("role_played", sa.String(length=255), nullable=True))
    op.add_column("projects", sa.Column("case_study_content", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("projects", sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"))

    op.execute("UPDATE projects SET project_type = 'case_study' WHERE project_type IS NULL")
    op.alter_column("projects", "project_type", nullable=False, server_default="case_study")
    op.alter_column("projects", "description", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    op.drop_column("projects", "display_order")
    op.drop_column("projects", "case_study_content")
    op.drop_column("projects", "role_played")
    op.drop_column("projects", "team_size")
    op.drop_column("projects", "duration")
    op.drop_column("projects", "demo_url")
    op.drop_column("projects", "screenshots")
    op.drop_column("projects", "hero_image_url")
    op.drop_column("projects", "project_type")

    bind = op.get_bind()
    project_type_enum.drop(bind, checkfirst=True)
