# PATH: varex_backend/app/models/faq.py
# FIX: Column name is_published (was "published" in migration — Bug 3.9)

import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class FAQ(Base):
    __tablename__ = "faqs"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question      = Column(Text, nullable=False)
    answer        = Column(Text, nullable=False)
    category      = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_published  = Column(Boolean, default=False, nullable=False)  # was "published" — FIXED
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
