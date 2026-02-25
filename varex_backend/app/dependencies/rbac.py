
# ──────────────────────────────────────────────────────────────────────────────
# app/dependencies/auth.py  –  VAREX Role-Based Access Control
# ──────────────────────────────────────────────────────────────────────────────

from uuid import UUID
from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_id


# ── OAuth2 scheme – points to login endpoint ──────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── 1. Core token decoder & user fetcher ──────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT, validate token type, and load the user from DB.
    Raises HTTP 401 on any failure.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        # Reject refresh tokens used as access tokens
        if payload.get("type") != "access":
            raise credentials_exc

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc

    except JWTError:
        raise credentials_exc

    user = await get_user_by_id(db, UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exc

    return user


# ── 2. Base active-user dependency (any authenticated user) ───────────────────
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Any authenticated & active user. Use for generic protected routes."""
    return current_user


# ── 3. Role hierarchy helper ───────────────────────────────────────────────────
# Define ascending privilege order so higher roles inherit lower ones.
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.guest:        0,
    UserRole.free_user:    1,
    UserRole.premium_user: 2,
    UserRole.admin:        3,
}


def _has_minimum_role(user: User, minimum: UserRole) -> bool:
    """Return True if the user's role rank >= required minimum rank."""
    return ROLE_HIERARCHY.get(user.role, 0) >= ROLE_HIERARCHY[minimum]


# ── 4. require_roles() – exact role whitelist ──────────────────────────────────
def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory: allow only users whose role is in the whitelist.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user: User = Depends(require_roles(UserRole.admin))):
            ...
    """
    async def _dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{[r.value for r in allowed_roles]}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _dependency


# ── 5. require_minimum_role() – hierarchy-aware ────────────────────────────────
def require_minimum_role(minimum_role: UserRole) -> Callable:
    """
    Dependency factory: allow the specified role AND any role above it.

    Admin  → passes for ANY minimum_role
    Premium → passes for premium_user or free_user minimum
    Free   → passes only for free_user minimum
    Guest  → passes only for guest minimum

    Usage:
        @router.get("/premium-content")
        async def premium_route(user: User = Depends(require_minimum_role(UserRole.premium_user))):
            ...
    """
    async def _dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not _has_minimum_role(current_user, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Minimum required role: {minimum_role.value}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _dependency


# ── 6. Pre-built convenience dependencies ─────────────────────────────────────

# Admin only – exact match
require_admin = require_roles(UserRole.admin)

# Premium or Admin – hierarchy aware
require_premium = require_minimum_role(UserRole.premium_user)

# Free, Premium, or Admin – any paid/registered user
require_free = require_minimum_role(UserRole.free_user)


# ── 7. Content-level access checker (runtime check on content object) ──────────
def check_content_access(content_access_level: str, user: User) -> None:
    """
    Call inside a route to gate a specific content item.

    content_access_level: "free" | "premium"

    Raises HTTP 403 if the user does not have the required level.
    """
    if content_access_level == "premium" and not _has_minimum_role(
        user, UserRole.premium_user
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required to access this content.",
        )


# ── 8. Usage examples (documentation only) ────────────────────────────────────
#
#  from app.dependencies.auth import (
#      get_current_active_user,
#      require_admin,
#      require_premium,
#      require_free,
#      require_roles,
#      require_minimum_role,
#      check_content_access,
#  )
#
#  # Any authenticated user
#  @router.get("/profile")
#  async def profile(user: User = Depends(get_current_active_user)):
#      return user
#
#  # Free content – free_user, premium_user, admin
#  @router.get("/content/free")
#  async def free_content(user: User = Depends(require_free)):
#      ...
#
#  # Premium content – premium_user, admin
#  @router.get("/content/premium")
#  async def premium_content(user: User = Depends(require_premium)):
#      ...
#
#  # Admin only
#  @router.delete("/users/{id}")
#  async def delete_user(user: User = Depends(require_admin)):
#      ...
#
#  # Custom multi-role whitelist
#  @router.get("/special")
#  async def special(user: User = Depends(require_roles(UserRole.admin, UserRole.premium_user))):
#      ...
#
#  # Per-object content gating inside a route
#  @router.get("/content/{id}")
#  async def get_content(id: UUID, user: User = Depends(get_current_active_user), db = Depends(get_db)):
#      content = await db_get_content(db, id)
#      check_content_access(content.access_level, user)   # raises 403 if needed
#      return content
