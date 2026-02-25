import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class WorkshopMode(str, enum.Enum):
    online  = "online"
    offline = "offline"
    hybrid  = "hybrid"

class WorkshopStatus(str, enum.Enum):
    upcoming   = "upcoming"
    open       = "open"
    full       = "full"
    completed  = "completed"

class Workshop(Base):
    __tablename__ = "workshops"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title           = Column(String(255), nullable=False)
    slug            = Column(String(255), unique=True, nullable=False)
    description     = Column(Text, nullable=False)
    curriculum      = Column(Text, nullable=True)  # markdown
    mode            = Column(Enum(WorkshopMode), default=WorkshopMode.online)
    status          = Column(Enum(WorkshopStatus), default=WorkshopStatus.upcoming)
    price_inr       = Column(Float, nullable=True)
    duration_hours  = Column(Integer, default=8)
    max_seats       = Column(Integer, default=30)
    seats_booked    = Column(Integer, default=0)
    scheduled_date  = Column(DateTime(timezone=True), nullable=True)
    trainer_id      = Column(UUID(as_uuid=True), ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True)
    is_published    = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class WorkshopRegistration(Base):
    __tablename__ = "workshop_registrations"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workshop_id  = Column(UUID(as_uuid=True), ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    razorpay_payment_id = Column(String(100), nullable=True)
    paid         = Column(Boolean, default=False)
    registered_at= Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
