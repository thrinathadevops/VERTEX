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
    title: str
    bio: Optional[str] = None
    years_experience: int = 0
    specializations: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    pricing: Optional[Any] = None
    available_for: Optional[List[str]] = None
    available_from: Optional[str] = None

class TeamMemberResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    title: str
    bio: Optional[str]
    years_experience: int
    specializations: Optional[List[str]]
    tools: Optional[List[str]]
    pricing: Optional[Any]
    available_for: Optional[List[str]]
    available_from: Optional[str]
    avatar_s3_key: Optional[str]
    linkedin_url: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
