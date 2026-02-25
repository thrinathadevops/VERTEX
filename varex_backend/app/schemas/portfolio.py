from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.portfolio import ProjectCategory

class ProjectCreate(BaseModel):
    title: str
    slug: str
    category: ProjectCategory
    summary: str
    description: str
    tech_stack: Optional[List[str]] = None
    outcomes: Optional[List[str]] = None
    github_url: Optional[str] = None
    is_featured: bool = False

class ProjectResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    category: ProjectCategory
    summary: str
    description: str
    tech_stack: Optional[List[str]]
    outcomes: Optional[List[str]]
    diagram_s3_key: Optional[str]
    github_url: Optional[str]
    is_featured: bool
    created_at: datetime
    model_config = {"from_attributes": True}
