from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.lead import LeadService, LeadStatus

class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    service_interest: LeadService
    message: Optional[str] = None
    preferred_slot: Optional[str] = None

class LeadResponse(BaseModel):
    id: UUID
    name: str
    email: str
    service_interest: LeadService
    status: LeadStatus
    created_at: datetime
    model_config = {"from_attributes": True}
