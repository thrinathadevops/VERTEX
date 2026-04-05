from datetime import datetime
import uuid

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: uuid.UUID
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    model_config = {"from_attributes": True}
