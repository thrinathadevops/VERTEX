from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class AvatarUpdatePayload(BaseModel):
    """
    Body for PATCH /team/{member_id}/avatar
    Sent by frontend after a successful S3 presigned upload.
    Both fields optional so either can be updated independently.
    """
    avatar_url: str | None = None   # CloudFront / S3 public URL
    s3_key:     str | None = None   # e.g. "avatar/uuid.png"
    
class TeamMemberCreate(BaseModel):
    name: str
    slug: str
    role: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_s3_key: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    is_published: bool = False
    specialisations: Optional[List[str]] = None
    enterprise_projects: Optional[List[str]] = None

class TeamMemberResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    role: str
    bio: Optional[str]
    avatar_url: Optional[str]
    avatar_s3_key: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    specialisations: Optional[List[str]]
    enterprise_projects: Optional[List[str]]
    display_order: int
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}
