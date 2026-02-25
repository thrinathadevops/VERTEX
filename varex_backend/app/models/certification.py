import uuid, enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class CertDomain(str, enum.Enum):
    devops   = "devops"
    security = "security"
    cloud    = "cloud"
    sap      = "sap"
    ai       = "ai"
    other    = "other"

class Certification(Base):
    __tablename__ = "certifications"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title           = Column(String(255), nullable=False)
    issuing_body    = Column(String(120), nullable=False)
    domain          = Column(Enum(CertDomain), nullable=False)
    badge_s3_key    = Column(String(512), nullable=True)
    credential_url  = Column(String(512), nullable=True)
    issued_date     = Column(Date, nullable=True)
    expiry_date     = Column(Date, nullable=True)
    team_member_id  = Column(UUID(as_uuid=True), ForeignKey("team_members.id", ondelete="CASCADE"), nullable=True)
    is_published    = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Achievement(Base):
    __tablename__ = "achievements"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    metric      = Column(String(120), nullable=True)  # "50+ engineers placed"
    year        = Column(String(10), nullable=True)
    icon_key    = Column(String(120), nullable=True)
    is_published= Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
