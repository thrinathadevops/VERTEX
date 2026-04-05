import asyncio
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import structured_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.auth_session import AuthSession
from app.models.user import User, UserRole
from app.schemas.session import SessionResponse
from app.schemas.user import UserCreate
from app.services.auth_protection import (
    clear_login_failures,
    enforce_rate_limit,
    get_progressive_delay_seconds,
    record_login_failure,
)
from app.services.auth_service import authenticate_user
from app.services.token_blacklist import blacklist_token, is_blacklisted

router = APIRouter()

_GENERIC_LOGIN_ERROR = "Invalid credentials"
_GENERIC_REGISTER_MESSAGE = "If the email can be used for registration, verification instructions will be sent shortly."

_reset_tokens: dict[str, dict] = {}
_verify_tokens: dict[str, dict] = {}


class LoginPayload(BaseModel):
    email: str
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
    token: str
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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _parse_uuid(value: str, error_detail: str = "Invalid session") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_detail) from exc


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth")


def _origin_allowed(origin: str) -> bool:
    allowed_origins = {settings.FRONTEND_URL, *settings.ALLOWED_ORIGINS}
    return origin.rstrip("/") in {item.rstrip("/") for item in allowed_origins}


def _enforce_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin and not _origin_allowed(origin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request origin not allowed")

    if not origin and referer:
        parsed = urlparse(referer)
        referer_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        if referer_origin and not _origin_allowed(referer_origin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request origin not allowed")


async def _send_email(to_email: str, subject: str, html: str) -> None:
    if not settings.SENDGRID_API_KEY:
        structured_logger.warning(f"Skipping email to {to_email} (no SendGrid API Key configured)")
        return

    import httpx

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": settings.FROM_EMAIL, "name": "VAREX Technologies"},
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


async def _find_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    return result.scalar_one_or_none()


def _store_verify_token(user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    _verify_tokens[token] = {
        "user_id": str(user_id),
        "expires_at": _utcnow() + timedelta(hours=24),
    }
    return token


def _store_reset_token(user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "user_id": str(user_id),
        "expires_at": _utcnow() + timedelta(hours=1),
    }
    return token


async def _ensure_min_auth_timing(started_at: float, extra_delay: float = 0.0) -> None:
    minimum_seconds = 0.35 + extra_delay
    remaining = minimum_seconds - (time.monotonic() - started_at)
    if remaining > 0:
        await asyncio.sleep(remaining)


async def _create_session_tokens(
    user: User,
    request: Request,
    db: AsyncSession,
) -> tuple[AuthSession, str, str]:
    refresh_expires_at = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = AuthSession(
        user_id=user.id,
        current_refresh_jti=str(uuid.uuid4()),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:512],
        expires_at=refresh_expires_at,
    )
    db.add(session)
    await db.flush()

    claims = {"sid": str(session.id), "sv": user.session_version}
    access_token = create_access_token(str(user.id), extra_claims=claims)
    refresh_token = create_refresh_token(
        str(user.id),
        extra_claims={**claims, "jti": session.current_refresh_jti},
    )
    return session, access_token, refresh_token


async def _revoke_session(session: AuthSession | None) -> None:
    if session and session.revoked_at is None:
        session.revoked_at = _utcnow()


@router.post("/register", status_code=201, summary="Register new user")
async def register(
    payload: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    normalized_email = _normalize_email(payload.email)
    enforce_rate_limit("register", _client_ip(request), normalized_email)

    existing = await _find_user_by_email(db, normalized_email)
    if existing:
        if not existing.is_verified:
            token = _store_verify_token(existing.id)
            verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            background_tasks.add_task(_send_verify_email, existing.email, existing.name, verify_url)
        return {"message": _GENERIC_REGISTER_MESSAGE}

    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.free_user,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = _store_verify_token(user.id)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    background_tasks.add_task(_send_verify_email, user.email, user.name, verify_url)
    structured_logger.info(f"auth.register.created email={user.email} user_id={user.id}")

    return {"message": _GENERIC_REGISTER_MESSAGE}


@router.get("/verify-email", summary="Verify email address via token link")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    entry = _verify_tokens.get(token)
    if not entry or _utcnow() > entry["expires_at"]:
        _verify_tokens.pop(token, None)
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")

    result = await db.execute(select(User).where(User.id == _parse_uuid(entry["user_id"], "Verification link is invalid or expired")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    _verify_tokens.pop(token, None)
    await db.commit()
    structured_logger.info(f"auth.verify.success email={user.email} user_id={user.id}")
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/login", summary="Login - sets httpOnly auth cookies")
async def login(
    payload: LoginPayload,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    started_at = time.monotonic()
    normalized_email = _normalize_email(payload.email)
    ip_address = _client_ip(request)

    enforce_rate_limit("login", ip_address, normalized_email)
    progressive_delay = get_progressive_delay_seconds(ip_address, normalized_email)

    user = await authenticate_user(normalized_email, payload.password, db)
    if not user or not user.is_verified:
        record_login_failure(ip_address, normalized_email)
        await _ensure_min_auth_timing(started_at, progressive_delay)
        structured_logger.warning(f"auth.login.failed email={normalized_email} ip={ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_GENERIC_LOGIN_ERROR)

    clear_login_failures(ip_address, normalized_email)
    session, access_token, refresh_token = await _create_session_tokens(user, request, db)
    _set_auth_cookies(response, access_token, refresh_token)
    await db.commit()

    await _ensure_min_auth_timing(started_at)
    structured_logger.info(f"auth.login.success email={user.email} user_id={user.id} session_id={session.id}")
    return {"id": str(user.id), "name": user.name, "email": user.email, "role": user.role.value}


@router.post("/refresh", summary="Rotate access token using httpOnly refresh cookie")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token. Please log in again.")

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    current_jti = payload.get("jti")
    session_id = payload.get("sid")
    user_id = payload.get("sub")
    if not current_jti or not session_id or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if await is_blacklisted(current_jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked. Please log in again.")

    user_result = await db.execute(select(User).where(User.id == _parse_uuid(user_id, "Invalid or expired refresh token")))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    if int(payload.get("sv", -1)) != user.session_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please log in again.")

    session_result = await db.execute(
        select(AuthSession).where(AuthSession.id == _parse_uuid(session_id, "Invalid or expired refresh token"), AuthSession.user_id == user.id)
    )
    auth_session = session_result.scalar_one_or_none()
    if (
        not auth_session
        or auth_session.revoked_at is not None
        or auth_session.current_refresh_jti != current_jti
        or auth_session.expires_at <= _utcnow()
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked. Please log in again.")

    ttl = max(0, int(payload["exp"] - datetime.utcnow().timestamp()))
    await blacklist_token(current_jti, ttl)

    auth_session.current_refresh_jti = str(uuid.uuid4())
    auth_session.last_seen_at = _utcnow()
    auth_session.expires_at = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    claims = {"sid": str(auth_session.id), "sv": user.session_version}
    new_access = create_access_token(str(user.id), extra_claims=claims)
    new_refresh = create_refresh_token(str(user.id), extra_claims={**claims, "jti": auth_session.current_refresh_jti})
    _set_auth_cookies(response, new_access, new_refresh)
    await db.commit()

    return {"message": "Token refreshed successfully"}


@router.post("/logout", summary="Logout current session")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    access_payload = decode_access_token(access_token) if access_token else None
    refresh_payload = decode_access_token(refresh_token) if refresh_token else None

    if access_payload and access_payload.get("jti") and access_payload.get("exp"):
        ttl = max(0, int(access_payload["exp"] - datetime.utcnow().timestamp()))
        await blacklist_token(access_payload["jti"], ttl)

    if refresh_payload and refresh_payload.get("jti") and refresh_payload.get("exp"):
        ttl = max(0, int(refresh_payload["exp"] - datetime.utcnow().timestamp()))
        await blacklist_token(refresh_payload["jti"], ttl)

    session_id = (access_payload or refresh_payload or {}).get("sid")
    if session_id:
        session_result = await db.execute(
            select(AuthSession).where(AuthSession.id == _parse_uuid(session_id), AuthSession.user_id == current_user.id)
        )
        await _revoke_session(session_result.scalar_one_or_none())
        await db.commit()

    _clear_auth_cookies(response)
    structured_logger.info(f"auth.logout user_id={current_user.id} session_id={session_id}")
    return {"message": "Logged out successfully"}


@router.get("/sessions", response_model=list[SessionResponse], summary="List active and recent sessions")
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    result = await db.execute(
        select(AuthSession).where(AuthSession.user_id == current_user.id).order_by(AuthSession.created_at.desc())
    )
    return result.scalars().all()


@router.post("/logout-all", summary="Logout all sessions for current user")
async def logout_all_sessions(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    current_user.session_version += 1
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == current_user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=_utcnow())
    )
    await db.commit()
    _clear_auth_cookies(response)
    structured_logger.warning(f"auth.logout_all user_id={current_user.id}")
    return {"message": "Logged out from all devices successfully"}


@router.delete("/sessions/{session_id}", summary="Revoke a specific session")
async def revoke_session(
    session_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    result = await db.execute(select(AuthSession).where(AuthSession.id == session_id, AuthSession.user_id == current_user.id))
    auth_session = result.scalar_one_or_none()
    if not auth_session:
        raise HTTPException(status_code=404, detail="Session not found")

    await _revoke_session(auth_session)
    await db.commit()
    return {"message": "Session revoked successfully"}


@router.post("/change-password", summary="Change password for authenticated user")
async def change_password(
    payload: ChangePasswordPayload,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _enforce_trusted_origin(request)
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.session_version += 1
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == current_user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=_utcnow())
    )
    await db.commit()
    structured_logger.warning(f"auth.password.changed user_id={current_user.id}")
    return {"message": "Password changed successfully. Please log in again on your devices."}


@router.post("/forgot-password", summary="Request a password reset email")
async def forgot_password(
    payload: ForgotPasswordPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    normalized_email = _normalize_email(payload.email)
    enforce_rate_limit("forgot-password", _client_ip(request), normalized_email)

    user = await _find_user_by_email(db, normalized_email)
    if user and user.is_active:
        token = _store_reset_token(user.id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(_send_reset_email, user.email, user.name, reset_url)

    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", summary="Reset password using emailed token")
async def reset_password(
    payload: ResetPasswordPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    enforce_rate_limit("reset-password", _client_ip(request), payload.token)
    entry = _reset_tokens.get(payload.token)
    if not entry or _utcnow() > entry["expires_at"]:
        _reset_tokens.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")

    result = await db.execute(select(User).where(User.id == _parse_uuid(entry["user_id"], "Reset token is invalid or expired")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    user.session_version += 1
    _reset_tokens.pop(payload.token, None)
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=_utcnow())
    )
    await db.commit()

    structured_logger.warning(f"auth.password.reset user_id={user.id}")
    return {"message": "Password reset successfully. You can now log in."}
