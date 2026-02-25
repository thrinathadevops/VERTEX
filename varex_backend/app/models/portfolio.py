import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean, JSON, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class ProjectCategory(str, enum.Enum):
    devops       = "devops"
    security     = "security"
    sap          = "sap"
    architecture = "architecture"
    ai_hiring    = "ai_hiring"

class Project(Base):
    __tablename__ = "projects"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title         = Column(String(255), nullable=False)
    slug          = Column(String(255), unique=True, nullable=False)
    category      = Column(Enum(ProjectCategory), nullable=False)
    summary       = Column(String(512), nullable=False)
    description   = Column(Text, nullable=False)
    tech_stack    = Column(JSON, nullable=True)   # ["Kubernetes","Terraform",...]
    outcomes      = Column(JSON, nullable=True)   # ["60% faster deploys",...]
    diagram_s3_key= Column(String(512), nullable=True)
    github_url    = Column(String(512), nullable=True)
    case_study_url= Column(String(512), nullable=True)
    is_featured   = Column(Boolean, default=False)
    is_published  = Column(Boolean, default=True)
    created_by    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
