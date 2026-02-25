# PATH: varex_backend/app/dependencies/auth.py
# REPLACE existing file completely.
# DELETE auth_b.py and varex_rbac.py after placing this.
# FIX: UserRole.premium_user -> UserRole.premium (Bug 1.3)
# FIX: JWT blacklist check on every request (Bug 5.1)
# FIX: Role hierarchy via _require_role factory

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.token_blacklist import is_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── Role hierarchy — higher index = more permissions ─────────────
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.guest:       0,
    UserRole.free_user:   1,
    UserRole.premium:     2,   # FIX: was UserRole.premium_user
    UserRole.enterprise:  3,
    UserRole.admin:       4,
}


# ── Core token → user resolver (single definition) ───────────────
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

    # Check JWT blacklist — enforces logout / token revocation
    jti = payload.get("jti")
    if jti and await is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise credentials_exception

    return user


# ── Public dependencies ───────────────────────────────────────────

async def get_current_active_user(
    user: User = Depends(_get_user_from_token),
) -> User:
    """Returns authenticated user. Raises 400 if account is inactive."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user


# ── Role-enforcement factory ──────────────────────────────────────

def _require_role(min_role: UserRole):
    """
    Returns a FastAPI dependency that checks the user has at least `min_role`.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(_ = Depends(require_admin)):
            ...
    """
    async def checker(
        user: User = Depends(get_current_active_user),
    ) -> User:
        user_level     = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 999)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{min_role.value}' role or higher",
            )
        return user
    return checker


# ── Convenience aliases ───────────────────────────────────────────
require_premium    = _require_role(UserRole.premium)
require_enterprise = _require_role(UserRole.enterprise)
require_admin      = _require_role(UserRole.admin)

# Backward-compatibility alias — used in some existing routers
get_current_user = get_current_active_user