# PATH: varex_backend/app/schemas/user.py
# FIX 3.19: UserResponse now includes updated_at

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

class UserCreate(BaseModel):
    name:     str
    email:    EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserResponse(BaseModel):
    id:          str
    name:        str
    email:       str
    role:        str
    is_active:   bool
    avatar_url:  Optional[str] = None
    company:     Optional[str] = None
    created_at:  datetime
    updated_at:  Optional[datetime] = None   # FIX 3.19

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name:       Optional[str] = None
    avatar_url: Optional[str] = None
    company:    Optional[str] = None

---

# PATH: varex_backend/app/schemas/subscription.py
# FIX 3.14: SubscriptionResponse now includes razorpay_payment_id and price_paid

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
    razorpay_payment_id:   Optional[str] = None   # FIX 3.14
    price_paid:            Optional[float] = None  # FIX 3.14
    created_at:            datetime

    model_config = {"from_attributes": True}

---

# PATH: varex_backend/app/schemas/content.py
# FIX 3.15: ContentCreate and ContentResponse include slug, category, is_published

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ContentCreate(BaseModel):
    title:        str
    slug:         Optional[str] = None
    body:         str
    category:     Optional[str] = None
    access_level: str = "free"
    is_published: bool = False

class ContentResponse(BaseModel):
    id:           UUID
    title:        str
    slug:         Optional[str] = None
    body:         str
    category:     Optional[str] = None
    access_level: str
    is_published: bool
    author_id:    Optional[UUID] = None
    created_at:   datetime
    updated_at:   Optional[datetime] = None

    model_config = {"from_attributes": True}

---

# PATH: varex_backend/app/schemas/team.py
# FIX 3.17: TeamMemberResponse includes github_url and enterprise_projects

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class AvatarUpdatePayload(BaseModel):
    avatar_url:   str
    avatar_s3_key: Optional[str] = None

class TeamMemberCreate(BaseModel):
    name:                str
    slug:                Optional[str] = None
    role:                str
    bio:                 Optional[str] = None
    avatar_url:          Optional[str] = None
    avatar_s3_key:       Optional[str] = None
    linkedin_url:        Optional[str] = None
    github_url:          Optional[str] = None
    specialisations:     Optional[list[str]] = None
    enterprise_projects: Optional[list[str]] = None
    display_order:       int = 0
    is_active:           bool = True
    is_published:        bool = False

class TeamMemberResponse(BaseModel):
    id:                  UUID
    name:                str
    slug:                Optional[str] = None
    role:                str
    bio:                 Optional[str] = None
    avatar_url:          Optional[str] = None
    linkedin_url:        Optional[str] = None
    github_url:          Optional[str] = None       # FIX 3.17
    specialisations:     Optional[list[str]] = None
    enterprise_projects: Optional[list[str]] = None # FIX 3.17
    display_order:       int = 0
    is_published:        bool
    created_at:          datetime

    model_config = {"from_attributes": True}

---

# PATH: varex_backend/app/schemas/portfolio.py
# FIX 3.16: ProjectCreate includes diagram_s3_key and case_study_url

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title:           str
    slug:            Optional[str] = None
    summary:         Optional[str] = None
    body:            Optional[str] = None
    category:        Optional[str] = None
    tech_stack:      Optional[list[str]] = None
    client_name:     Optional[str] = None
    diagram_s3_key:  Optional[str] = None   # FIX 3.16
    case_study_url:  Optional[str] = None   # FIX 3.16
    is_published:    bool = False

class ProjectResponse(BaseModel):
    id:              UUID
    title:           str
    slug:            Optional[str] = None
    summary:         Optional[str] = None
    category:        Optional[str] = None
    tech_stack:      Optional[list] = None
    client_name:     Optional[str] = None
    diagram_s3_key:  Optional[str] = None
    case_study_url:  Optional[str] = None
    is_published:    bool
    created_at:      datetime

    model_config = {"from_attributes": True}

---

# PATH: varex_backend/app/schemas/workshop.py
# FIX 3.18: WorkshopCreate includes status, trainer_id, is_published

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class WorkshopCreate(BaseModel):
    title:          str
    slug:           Optional[str] = None
    description:    Optional[str] = None
    mode:           str = "online"
    price:          float = 0.0
    max_seats:      int
    status:         str = "upcoming"              # FIX 3.18
    trainer_id:     Optional[UUID] = None         # FIX 3.18
    is_published:   bool = False                  # FIX 3.18
    scheduled_date: Optional[datetime] = None

class WorkshopResponse(BaseModel):
    id:             UUID
    title:          str
    slug:           Optional[str] = None
    description:    Optional[str] = None
    mode:           str
    price:          float
    max_seats:      int
    seats_booked:   int
    status:         str
    is_published:   bool
    scheduled_date: Optional[datetime] = None
    created_at:     datetime

    model_config = {"from_attributes": True}

class WorkshopRegistrationResponse(BaseModel):
    id:          UUID
    workshop_id: UUID
    user_id:     UUID
    paid:        bool = False
    created_at:  datetime

    model_config = {"from_attributes": True}
