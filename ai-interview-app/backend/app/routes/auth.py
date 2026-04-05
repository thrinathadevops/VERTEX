"""
Authentication Routes
─────────────────────
Register, login, bootstrap admin, and profile endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..auth.jwt_handler import create_access_token, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import (
    PasswordChangeRequest,
    TokenResponse,
    UserLogin,
    UserProfile,
    UserRegister,
    VerificationRequest,
)
from ..services.email_verification import (
    issue_verification_token,
    mark_email_verified,
    normalize_email,
    send_verification_email,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _bootstrap_admin(db: Session) -> User:
    user = User(
        email="admin",
        full_name="Administrator",
        hashed_password=hash_password("admin"),
        role="super_admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _find_user_by_identifier(db: Session, identifier: str) -> User | None:
    normalized = normalize_email(identifier)
    return db.scalar(select(User).where(User.email == normalized))


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    normalized_email = normalize_email(payload.email)
    existing = db.scalar(
        select(User).where(User.email == normalized_email)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=normalized_email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="candidate",
        company_name=payload.company_name,
        company_code=payload.company_code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        full_name=user.full_name,
        must_change_password=False,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return JWT token."""
    identifier = payload.username_or_email.strip()
    admin_exists = db.scalar(select(User).where(User.role == "super_admin"))
    if not admin_exists and identifier == "admin" and payload.password == "admin":
        user = _bootstrap_admin(db)
        token = create_access_token({"sub": user.id, "role": user.role, "bootstrap": True})
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            role=user.role,
            full_name=user.full_name,
            must_change_password=True,
        )

    user = _find_user_by_identifier(db, identifier)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    must_change_password = user.role == "super_admin" and verify_password("admin", user.hashed_password)
    token = create_access_token({"sub": user.id, "role": user.role, "bootstrap": must_change_password})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        full_name=user.full_name,
        must_change_password=must_change_password,
    )


@router.get("/profile", response_model=UserProfile)
def get_profile(user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_name=user.company_name,
        free_mock_used=user.free_mock_used,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/request-verification")
async def request_verification(
    payload: VerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_email(payload.email)
    token = issue_verification_token(db, normalized_email)
    background_tasks.add_task(send_verification_email, normalized_email, token)
    return {"message": "If the email can be verified, a verification link has been sent."}


@router.get("/verify-email")
def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    email = mark_email_verified(db, token)
    if not email:
        return JSONResponse(
            status_code=400,
            content={"message": "Verification link is invalid or expired."},
        )
    return {"message": "Email verified successfully.", "email": email}


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password must match.")

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if user.role == "super_admin" and verify_password("admin", user.hashed_password) and payload.current_password != "admin":
        raise HTTPException(status_code=400, detail="Bootstrap admin password must be changed from the default password.")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully."}
