from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.workshop import WorkshopMode, WorkshopStatus

class WorkshopRegistrationResponse(BaseModel):
    """
    Returned by GET /workshops/{workshop_id}/registrations (admin only).
    Add this class to your existing schemas/workshop.py file.
    """
    model_config = ConfigDict(from_attributes=True)

    id:          UUID
    workshop_id: UUID
    user_id:     UUID
    created_at:  datetime

    # Optional: include user info if you join User in the query
    # user_name:  str | None = None
    # user_email: str | None = None


class WorkshopCreate(BaseModel):
    title: str
    slug: str
    description: str
    curriculum: Optional[str] = None
    mode: WorkshopMode = WorkshopMode.online
    price_inr: Optional[float] = None
    duration_hours: int = 8
    max_seats: int = 30
    scheduled_date: Optional[datetime] = None

class WorkshopResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str
    mode: WorkshopMode
    status: WorkshopStatus
    price_inr: Optional[float]
    duration_hours: int
    max_seats: int
    seats_booked: int
    scheduled_date: Optional[datetime]
    is_published: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class WorkshopRegisterResponse(BaseModel):
    id: UUID
    workshop_id: UUID
    user_id: UUID
    paid: bool
    registered_at: datetime
    model_config = {"from_attributes": True}
