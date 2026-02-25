# PATH: varex_backend/app/models/content.py
# FIX: Added slug, category, is_published columns (Bug 3.1, 3.2)

import uuid
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

import enum

class AccessLevel(str, enum.Enum):
    free    = "free"
    premium = "premium"


class Content(Base):
    __tablename__ = "content"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title        = Column(String(500), nullable=False)
    slug         = Column(String(500), unique=True, nullable=True)      # ADDED (Bug 3.1)
    body         = Column(Text, nullable=False)
    category     = Column(String(100), nullable=True)                   # ADDED (Bug 3.1)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.free, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)       # ADDED (Bug 3.2)
    author_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", back_populates="content_items")
