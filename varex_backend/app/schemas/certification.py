from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.certification import CertDomain

class CertificationCreate(BaseModel):
    title: str
    issuing_body: str
    domain: CertDomain
    credential_url: Optional[str] = None
    issued_date: Optional[date] = None
    expiry_date: Optional[date] = None
    team_member_id: Optional[UUID] = None

class CertificationResponse(BaseModel):
    id: UUID
    title: str
    issuing_body: str
    domain: CertDomain
    credential_url: Optional[str]
    issued_date: Optional[date]
    expiry_date: Optional[date]
    badge_s3_key: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class AchievementCreate(BaseModel):
    title: str
    description: str
    metric: Optional[str] = None
    year: Optional[str] = None

class AchievementResponse(BaseModel):
    id: UUID
    title: str
    description: str
    metric: Optional[str]
    year: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
