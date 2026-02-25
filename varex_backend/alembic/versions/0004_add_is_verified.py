# PATH: varex_backend/alembic/versions/0004_add_is_verified.py
"""add is_verified to users

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

revision      = "0004"
down_revision = "0003"
branch_labels = None
depends_on    = None

def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"))

def downgrade() -> None:
    op.drop_column("users", "is_verified")
