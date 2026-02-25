from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.subscription import PlanType, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    plan_type: PlanType


class SubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_type: PlanType
    start_date: datetime
    expiry_date: Optional[datetime]
    status: SubscriptionStatus

    model_config = {"from_attributes": True}
