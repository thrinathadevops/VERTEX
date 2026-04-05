"""add_auth_sessions_and_session_version

Revision ID: 9d5b7d3c4e21
Revises: 59c0c644f1fa
Create Date: 2026-04-05 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision: str = "9d5b7d3c4e21"
down_revision: Union[str, None] = "59c0c644f1fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("users", "session_version", server_default=None)

    op.create_table(
        "auth_sessions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_refresh_jti", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_auth_sessions_current_refresh_jti"), "auth_sessions", ["current_refresh_jti"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_sessions_current_refresh_jti"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_column("users", "session_version")
