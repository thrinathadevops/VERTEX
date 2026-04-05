# PATH: varex_backend/app/services/auth_service.py
# FIX: Timing-safe password check — always calls verify_password (Bug 2.4)

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User

# Dummy hash used when user not found — prevents timing leak
_DUMMY_HASH = "$2b$12$eImiTXuWVxfM37uY4JANjQe5s/9l5mb/KCm7fBj0FJrBm.0ypVRoe"


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    user = result.scalar_one_or_none()

    # Always run verify_password to prevent timing-based user enumeration (Bug 2.4)
    hash_to_check = user.hashed_password if user else _DUMMY_HASH
    is_valid = verify_password(password, hash_to_check)

    if not user or not is_valid or not user.is_active:
        return None
    return user
