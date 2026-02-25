# PATH: varex_backend/app/api/v1/auth.py
# FULL FINAL FILE — replace existing completely
# Fixes applied:
#   - logout defined once (with Response cookie clearing)
#   - login defined once (with httpOnly cookies)
#   - /refresh fully implemented using Request.cookies (not a stub)
#   - /refresh unused imports removed (Request was imported but never used)
#   - RefreshPayload schema removed (token comes from httpOnly cookie, not body)
#   - _send_email deduplicates all email logic into one helper

import re
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user, oauth2_scheme
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.services.auth_service import authenticate_user
from app.services.token_blacklist import blacklist_token, is_blacklisted

router = APIRouter()

# ── In-memory token stores ────────────────────────────────────────
# NOTE: These are per-process. For multi-instance / multi-worker deployments,
#       migrate both dicts to Redis using the same pattern as token_blacklist.py
_reset_tokens:  dict[str, dict] = {}   # token -> {user_id, expires_at}
_verify_tokens: dict[str, str]  = {}   # token -> user_id


# ═══════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class LoginPayload(BaseModel):
    email:    str
    password: str


class ChangePasswordPayload(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Must contain at least one special character")
        return v


class ForgotPasswordPayload(BaseModel):
    email: str


class ResetPasswordPayload(BaseModel):
    token:        str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain a digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Must contain a special character")
        return v


# ═══════════════════════════════════════════════════════════════════
# COOKIE HELPERS
# ═══════════════════════════════════════════════════════════════════

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",   # scoped — browser only sends it to this path
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token",  path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")


# ═══════════════════════════════════════════════════════════════════
# EMAIL HELPERS
# ═══════════════════════════════════════════════════════════════════

async def _send_email(to_email: str, subject: str, html: str) -> None:
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from":    {"email": settings.FROM_EMAIL, "name": "VAREX Technologies"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
        )


async def _send_verify_email(to_email: str, name: str, verify_url: str) -> None:
    await _send_email(
        to_email,
        subject="Verify your VAREX account",
        html=f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
          <h2>Welcome to VAREX, {name}!</h2>
          <p>Click the button below to verify your email address and activate your account.</p>
          <a href="{verify_url}"
             style="background:#0ea5e9;color:#fff;padding:12px 24px;border-radius:8px;
                    text-decoration:none;display:inline-block;margin:16px 0;font-weight:600">
            Verify Email
          </a>
          <p style="color:#888;font-size:13px">This link is valid for 24 hours.</p>
          <p>&#8212; VAREX Technologies</p>
        </div>
        """,
    )


async def _send_reset_email(to_email: str, name: str, reset_url: str) -> None:
    await _send_email(
        to_email,
        subject="Reset your VAREX password",
        html=f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
          <h2>Hi {name},</h2>
          <p>Click below to reset your password. This link expires in 1 hour.</p>
          <a href="{reset_url}"
             style="background:#0ea5e9;color:#fff;padding:12px 24px;border-radius:8px;
                    text-decoration:none;display:inline-block;margin:16px 0;font-weight:600">
            Reset Password
          </a>
          <p style="color:#888;font-size:13px">If you did not request this, ignore this email safely.</p>
          <p>&#8212; VAREX Technologies</p>
        </div>
        """,
    )


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

# ── POST /register ────────────────────────────────────────────────
@router.post("/register", status_code=201, summary="Register new user")
async def register(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name            = payload.name,
        email           = payload.email,
        hashed_password = get_password_hash(payload.password),
        role            = UserRole.free_user,
        is_active       = True,
        is_verified     = False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token      = secrets.token_urlsafe(32)
    verify_url = f"https://varextech.in/verify-email?token={token}"
    _verify_tokens[token] = str(user.id)
    background_tasks.add_task(_send_verify_email, user.email, user.name, verify_url)

    return {"message": "Registration successful. Please check your email to verify your account."}


# ── GET /verify-email ─────────────────────────────────────────────
@router.get("/verify-email", summary="Verify email address via token link")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    user_id = _verify_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    del _verify_tokens[token]
    await db.commit()
    return {"message": "Email verified successfully. You can now log in."}


# ── POST /login ───────────────────────────────────────────────────
@router.post("/login", summary="Login — sets httpOnly auth cookies")
async def login(
    payload: LoginPayload,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(payload.email, payload.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    access_token  = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "id":    str(user.id),
        "name":  user.name,
        "email": user.email,
        "role":  user.role.value,
    }


# ── POST /refresh ─────────────────────────────────────────────────
@router.post("/refresh", summary="Rotate access token using httpOnly refresh cookie")
async def refresh_token(
    request:  Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token. Please log in again.",
        )

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Reject if this refresh token was explicitly blacklisted (e.g. logout on another device)
    jti = payload.get("jti")
    if jti and await is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked. Please log in again.",
        )

    user_id = payload.get("sub")
    result  = await db.execute(select(User).where(User.id == user_id))
    user    = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access  = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, new_access, new_refresh)

    return {"message": "Token refreshed successfully"}


# ── POST /logout ──────────────────────────────────────────────────
@router.post("/logout", summary="Logout — blacklist JWT and clear cookies")
async def logout(
    request:  Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
):
    # Blacklist the access token from the Authorization header (if present)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token   = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                ttl = max(0, int(exp - datetime.utcnow().timestamp()))
                await blacklist_token(jti, ttl)

    # Also blacklist the refresh token from the cookie
    refresh = request.cookies.get("refresh_token")
    if refresh:
        rpayload = decode_access_token(refresh)
        if rpayload:
            rjti = rpayload.get("jti")
            rexp = rpayload.get("exp")
            if rjti and rexp:
                ttl = max(0, int(rexp - datetime.utcnow().timestamp()))
                await blacklist_token(rjti, ttl)

    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


# ── POST /change-password ─────────────────────────────────────────
@router.post("/change-password", summary="Change password for authenticated user")
async def change_password(
    payload: ChangePasswordPayload,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


# ── POST /forgot-password ─────────────────────────────────────────
@router.post("/forgot-password", summary="Request a password reset email")
async def forgot_password(
    payload: ForgotPasswordPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user   = result.scalar_one_or_none()

    # Always return 200 — prevents user enumeration attacks
    if user and user.is_active:
        token     = secrets.token_urlsafe(32)
        reset_url = f"https://varextech.in/reset-password?token={token}"
        _reset_tokens[token] = {
            "user_id":    str(user.id),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }
        background_tasks.add_task(_send_reset_email, user.email, user.name, reset_url)

    return {"message": "If that email exists, a reset link has been sent."}


# ── POST /reset-password ──────────────────────────────────────────
@router.post("/reset-password", summary="Reset password using emailed token")
async def reset_password(
    payload: ResetPasswordPayload,
    db: AsyncSession = Depends(get_db),
):
    entry = _reset_tokens.get(payload.token)
    if not entry or datetime.utcnow() > entry["expires_at"]:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")

    result = await db.execute(select(User).where(User.id == entry["user_id"]))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    del _reset_tokens[payload.token]   # one-time use — consumed immediately
    await db.commit()
    return {"message": "Password reset successfully. You can now log in."}