# PATH: varex_backend/app/schemas/content.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ContentCreate(BaseModel):
    title:        str
    slug:         Optional[str] = None
    body:         str
    category:     Optional[str] = None
    access_level: str = "free"
    is_published: bool = False

class ContentResponse(BaseModel):
    id:           UUID
    title:        str
    slug:         Optional[str] = None
    body:         str
    category:     Optional[str] = None
    access_level: str
    is_published: bool
    author_id:    Optional[UUID] = None
    created_at:   datetime
    updated_at:   Optional[datetime] = None

    model_config = {"from_attributes": True}
