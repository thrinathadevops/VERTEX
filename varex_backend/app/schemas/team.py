# PATH: varex_backend/app/schemas/team.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class AvatarUpdatePayload(BaseModel):
    avatar_url:   str
    avatar_s3_key: Optional[str] = None

class TeamMemberCreate(BaseModel):
    name:                str
    slug:                Optional[str] = None
    role:                str
    bio:                 Optional[str] = None
    avatar_url:          Optional[str] = None
    avatar_s3_key:       Optional[str] = None
    linkedin_url:        Optional[str] = None
    github_url:          Optional[str] = None
    specialisations:     Optional[list[str]] = None
    enterprise_projects: Optional[list[str]] = None
    display_order:       int = 0
    is_active:           bool = True
    is_published:        bool = False

class TeamMemberResponse(BaseModel):
    id:                  UUID
    name:                str
    slug:                Optional[str] = None
    role:                str
    bio:                 Optional[str] = None
    avatar_url:          Optional[str] = None
    linkedin_url:        Optional[str] = None
    github_url:          Optional[str] = None
    specialisations:     Optional[list[str]] = None
    enterprise_projects: Optional[list[str]] = None
    display_order:       int = 0
    is_published:        bool
    created_at:          datetime
    updated_at:          Optional[datetime] = None

    model_config = {"from_attributes": True}
