# PATH: varex_backend/app/schemas/workshop.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.workshop import WorkshopMode, WorkshopStatus


class WorkshopCreate(BaseModel):
    title:          str
    slug:           Optional[str] = None
    description:    Optional[str] = None
    mode:           str = "online"
    price:          float = 0.0
    max_seats:      int
    status:         str = "upcoming"
    trainer_id:     Optional[UUID] = None
    is_published:   bool = False
    scheduled_date: Optional[datetime] = None

class WorkshopResponse(BaseModel):
    id:             UUID
    title:          str
    slug:           Optional[str] = None
    description:    Optional[str] = None
    mode:           str
    price:          float
    max_seats:      int
    seats_booked:   int
    status:         str
    is_published:   bool
    scheduled_date: Optional[datetime] = None
    created_at:     datetime
    trainer_id:     Optional[UUID] = None

    model_config = {"from_attributes": True}

class WorkshopRegistrationResponse(BaseModel):
    id:          UUID
    workshop_id: UUID
    user_id:     UUID
    paid:        bool = False
    created_at:  datetime

    model_config = {"from_attributes": True}
