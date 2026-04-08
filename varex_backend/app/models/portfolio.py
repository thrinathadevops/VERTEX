import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean, JSON, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class ProjectCategory(str, enum.Enum):
    devops       = "devops"
    security     = "security"
    sap          = "sap"
    architecture = "architecture"
    ai_hiring    = "ai_hiring"


class ProjectType(str, enum.Enum):
    client_work      = "client_work"
    personal_project = "personal_project"
    internal_product = "internal_product"
    case_study       = "case_study"

class Project(Base):
    __tablename__ = "projects"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title         = Column(String(255), nullable=False)
    slug          = Column(String(255), unique=True, nullable=False)
    category      = Column(Enum(ProjectCategory), nullable=False)
    project_type  = Column(Enum(ProjectType), nullable=False, default=ProjectType.case_study)
    summary       = Column(String(512), nullable=False)
    description   = Column(Text, nullable=False)
    tech_stack    = Column(JSON, nullable=True)   # ["Kubernetes","Terraform",...]
    outcomes      = Column(JSON, nullable=True)   # ["60% faster deploys",...]
    hero_image_url = Column(String(512), nullable=True)
    screenshots   = Column(JSON, nullable=True)   # ["https://...", ...]
    diagram_s3_key= Column(String(512), nullable=True)
    github_url    = Column(String(512), nullable=True)
    demo_url      = Column(String(512), nullable=True)
    case_study_url= Column(String(512), nullable=True)
    client_name   = Column(String(255), nullable=True)
    duration      = Column(String(120), nullable=True)
    team_size     = Column(Integer, nullable=True)
    role_played   = Column(String(255), nullable=True)
    case_study_content = Column(JSON, nullable=True)
    is_featured   = Column(Boolean, default=False)
    is_published  = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_by    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
