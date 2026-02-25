# PATH: varex_backend/app/dependencies/auth.py
# FIX: Single canonical auth module — DELETE auth_b.py and varex_rbac.py
# FIX: All UserRole.premium_user -> UserRole.premium
# FIX: Timing-safe password check (Bug 2.4 addressed in auth_service.py)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── ROLE HIERARCHY ────────────────────────────────────────────────
# Higher index = more permissions
ROLE_HIERARCHY = {
    UserRole.guest:       0,
    UserRole.free_user:   1,
    UserRole.premium:     2,   # was premium_user — FIXED
    UserRole.enterprise:  3,
    UserRole.admin:       4,
}


async def _get_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    user: User = Depends(_get_user_from_token),
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user


def _require_role(min_role: UserRole):
    """Factory: returns a FastAPI dependency that enforces a minimum role."""
    async def checker(user: User = Depends(get_current_active_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 999)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role.value} role or higher",
            )
        return user
    return checker


# ── Convenience dependency aliases ───────────────────────────────
require_premium    = _require_role(UserRole.premium)
require_enterprise = _require_role(UserRole.enterprise)
require_admin      = _require_role(UserRole.admin)

# Alias for backwards compatibility
get_current_user = get_current_active_user
