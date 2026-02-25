# PATH: varex_backend/app/schemas/portfolio.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title:           str
    slug:            Optional[str] = None
    summary:         Optional[str] = None
    body:            Optional[str] = None
    category:        Optional[str] = None
    tech_stack:      Optional[list[str]] = None
    client_name:     Optional[str] = None
    diagram_s3_key:  Optional[str] = None
    case_study_url:  Optional[str] = None
    is_published:    bool = False

class ProjectResponse(BaseModel):
    id:              UUID
    title:           str
    slug:            Optional[str] = None
    summary:         Optional[str] = None
    category:        Optional[str] = None
    tech_stack:      Optional[list] = None
    client_name:     Optional[str] = None
    diagram_s3_key:  Optional[str] = None
    case_study_url:  Optional[str] = None
    is_published:    bool
    created_at:      datetime

    model_config = {"from_attributes": True}
