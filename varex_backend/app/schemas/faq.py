from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str = "general"
    display_order: int = 0

class FAQResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    category: Optional[str] = None
    display_order: int
    created_at: datetime
    model_config = {"from_attributes": True}
