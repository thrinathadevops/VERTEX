from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.faq import FAQCategory

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: FAQCategory = FAQCategory.general
    order_rank: int = 0

class FAQResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    category: FAQCategory
    order_rank: int
    created_at: datetime
    model_config = {"from_attributes": True}
