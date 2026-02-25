"""add_missing_database_indexes

Revision ID: 59c0c644f1fa
Revises: 0004
Create Date: 2026-02-25 17:21:47.187332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59c0c644f1fa'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)

    # Workshops
    op.create_index(op.f("ix_workshops_trainer_id"), "workshops", ["trainer_id"], unique=False)
    
    # Workshop Registrations (assuming table is workshop_registrations)
    op.create_index(op.f("ix_workshop_registrations_user_id"), "workshop_registrations", ["user_id"], unique=False)
    op.create_index(op.f("ix_workshop_registrations_workshop_id"), "workshop_registrations", ["workshop_id"], unique=False)

    # Portfolio
    op.create_index(op.f("ix_projects_created_by"), "projects", ["created_by"], unique=False)

    # Interview / ATS (Assuming table names from models output)
    op.create_index(op.f("ix_job_descriptions_created_by"), "job_descriptions", ["created_by"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_job_id"), "candidate_profiles", ["job_description_id"], unique=False)
    op.create_index(op.f("ix_interview_sessions_job_id"), "interview_sessions", ["job_description_id"], unique=False)
    op.create_index(op.f("ix_interview_sessions_candidate_id"), "interview_sessions", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_interview_turns_session_id"), "interview_turns", ["session_id"], unique=False)

    # Content
    op.create_index(op.f("ix_content_author_id"), "content", ["author_id"], unique=False)

    # Team
    op.create_index(op.f("ix_certifications_team_member_id"), "certifications", ["team_member_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    
    op.drop_index(op.f("ix_workshops_trainer_id"), table_name="workshops")
    op.drop_index(op.f("ix_workshop_registrations_user_id"), table_name="workshop_registrations")
    op.drop_index(op.f("ix_workshop_registrations_workshop_id"), table_name="workshop_registrations")
    
    op.drop_index(op.f("ix_projects_created_by"), table_name="projects")
    
    op.drop_index(op.f("ix_job_descriptions_created_by"), table_name="job_descriptions")
    op.drop_index(op.f("ix_candidate_profiles_job_id"), table_name="candidate_profiles")
    op.drop_index(op.f("ix_interview_sessions_job_id"), table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_sessions_candidate_id"), table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_turns_session_id"), table_name="interview_turns")
    
    op.drop_index(op.f("ix_content_author_id"), table_name="content")
    
    op.drop_index(op.f("ix_certifications_team_member_id"), table_name="certifications")
