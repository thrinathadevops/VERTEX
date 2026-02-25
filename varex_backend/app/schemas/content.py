from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.models.content import AccessLevel


class ContentCreate(BaseModel):
    title: str
    body: str
    access_level: AccessLevel = AccessLevel.free


class ContentResponse(BaseModel):
    id: UUID
    title: str
    body: str
    access_level: AccessLevel
    created_at: datetime

    model_config = {"from_attributes": True}
