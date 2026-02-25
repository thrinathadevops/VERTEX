# PATH: varex_backend/app/schemas/user.py
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
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
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
    updated_at:  Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name:       Optional[str] = None
    avatar_url: Optional[str] = None
    company:    Optional[str] = None
