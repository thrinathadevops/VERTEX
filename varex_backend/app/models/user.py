import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserRole(str, enum.Enum):
    guest      = "guest"          # no login — public only
    free_user  = "free_user"      # registered, free plan
    premium    = "premium"        # paid subscriber
    enterprise = "enterprise"     # enterprise client (custom)
    admin      = "admin"          # full access

class User(Base):
    __tablename__ = "users"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(120), nullable=False)
    email        = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role         = Column(Enum(UserRole), default=UserRole.free_user)
    company      = Column(String(120), nullable=True)   # for enterprise
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    content_items = relationship("Content", back_populates="author", cascade="all, delete-orphan")
    is_verified = Column(Boolean, default=False, nullable=False)
