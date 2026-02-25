# PATH: varex_backend/app/models/team.py
# FIX: Added display_order column (Bug 1.6)
# FIX: Added avatar_url column (Bug 1.7)
# FIX: Added github_url, is_active, is_published, updated_at (Bug 3.6)

import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base_class import Base


class TeamMember(Base):
    __tablename__ = "team_members"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name                = Column(String(255), nullable=False)
    slug                = Column(String(255), unique=True, nullable=True)
    role                = Column(String(255), nullable=False)            # Job title
    bio                 = Column(Text, nullable=True)
    avatar_url          = Column(Text, nullable=True)                    # ADDED (Bug 1.7)
    avatar_s3_key       = Column(Text, nullable=True)
    linkedin_url        = Column(Text, nullable=True)
    github_url          = Column(Text, nullable=True)                    # ADDED (Bug 3.6)
    specialisations     = Column(ARRAY(String), nullable=True)
    enterprise_projects = Column(ARRAY(String), nullable=True)           # ADDED (Bug 3.6)
    display_order       = Column(Integer, default=0, nullable=False)     # ADDED (Bug 1.6)
    is_active           = Column(Boolean, default=True, nullable=False)  # ADDED (Bug 3.6)
    is_published        = Column(Boolean, default=False, nullable=False) # ADDED (Bug 3.6)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())  # ADDED (Bug 3.6)
