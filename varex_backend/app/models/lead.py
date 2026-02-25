import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class LeadService(str, enum.Enum):
    devsecops      = "devsecops"
    cybersecurity  = "cybersecurity"
    sap_sd         = "sap_sd"
    ai_hiring      = "ai_hiring"
    consulting     = "consulting"
    training       = "training"
    workshop       = "workshop"
    other          = "other"

class LeadStatus(str, enum.Enum):
    new        = "new"
    contacted  = "contacted"
    qualified  = "qualified"
    converted  = "converted"
    closed     = "closed"

class ConsultationLead(Base):
    __tablename__ = "consultation_leads"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name             = Column(String(120), nullable=False)
    email            = Column(String(255), nullable=False)
    phone            = Column(String(30), nullable=True)
    company          = Column(String(120), nullable=True)
    service_interest = Column(Enum(LeadService), nullable=False)
    message          = Column(Text, nullable=True)
    preferred_slot   = Column(String(50), nullable=True)   # "Mon 10am IST"
    status           = Column(Enum(LeadStatus), default=LeadStatus.new)
    utm_source       = Column(String(100), nullable=True)
    is_free_consult  = Column(Boolean, default=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
