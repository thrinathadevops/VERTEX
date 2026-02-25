# PATH: varex_backend/app/schemas/subscription.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.models.subscription import PlanType, SubscriptionStatus

class SubscriptionCreate(BaseModel):
    plan_type: PlanType

class ActivateSubscription(BaseModel):
    subscription_id:     UUID
    razorpay_payment_id: str
    razorpay_signature:  str

class SubscriptionResponse(BaseModel):
    id:                    UUID
    user_id:               UUID
    plan_type:             PlanType
    status:                SubscriptionStatus
    start_date:            Optional[datetime] = None
    expiry_date:           Optional[datetime] = None
    razorpay_order_id:     Optional[str] = None
    razorpay_payment_id:   Optional[str] = None
    price_paid:            Optional[float] = None
    created_at:            datetime

    model_config = {"from_attributes": True}
