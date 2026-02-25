import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class PlanType(str, enum.Enum):
    free       = "free"           # ₹0  – basic access
    monthly    = "monthly"        # ₹999–1999/mo
    quarterly  = "quarterly"      # ₹2999–4999/qtr
    enterprise = "enterprise"     # custom pricing

class SubscriptionStatus(str, enum.Enum):
    active    = "active"
    expired   = "expired"
    cancelled = "cancelled"
    trial     = "trial"

PLAN_PRICES_INR = {
    PlanType.free:       0,
    PlanType.monthly:    1499,
    PlanType.quarterly:  3999,
    PlanType.enterprise: 0,     # set per client
}

class Subscription(Base):
    __tablename__ = "subscriptions"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_type    = Column(Enum(PlanType), default=PlanType.free)
    status       = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active)
    price_paid   = Column(Float, nullable=True)
    start_date   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expiry_date  = Column(DateTime(timezone=True), nullable=True)
    razorpay_order_id   = Column(String(120), nullable=True)
    razorpay_payment_id = Column(String(120), nullable=True)
    user         = relationship("User", back_populates="subscription")
