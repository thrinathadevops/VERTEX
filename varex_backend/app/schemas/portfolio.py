# PATH: varex_backend/app/schemas/portfolio.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCaseStudyContent(BaseModel):
    problem_statement: Optional[str] = None
    solution_approach: Optional[str] = None
    architecture_overview: Optional[str] = None
    security_considerations: Optional[str] = None
    deployment_flow: Optional[str] = None
    results: Optional[str] = None
    lessons_learned: Optional[str] = None

class ProjectCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    summary: str
    description: str
    category: str
    project_type: str = "case_study"
    tech_stack: Optional[list[str]] = None
    outcomes: Optional[list[str]] = None
    hero_image_url: Optional[str] = None
    screenshots: Optional[list[str]] = None
    client_name: Optional[str] = None
    duration: Optional[str] = None
    team_size: Optional[int] = None
    role_played: Optional[str] = None
    diagram_s3_key: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    case_study_url: Optional[str] = None
    case_study_content: Optional[ProjectCaseStudyContent] = None
    is_featured: bool = False
    is_published: bool = False
    display_order: int = 0

class ProjectResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    summary: str
    description: str
    category: str
    project_type: str
    tech_stack: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    hero_image_url: Optional[str] = None
    screenshots: list[str] = Field(default_factory=list)
    client_name: Optional[str] = None
    duration: Optional[str] = None
    team_size: Optional[int] = None
    role_played: Optional[str] = None
    diagram_s3_key: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    case_study_url: Optional[str] = None
    case_study_content: Optional[ProjectCaseStudyContent] = None
    is_featured: bool
    is_published: bool
    display_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
