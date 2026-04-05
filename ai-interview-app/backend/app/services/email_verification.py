from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models import EmailVerification


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_verification_record(db: Session, email: str) -> EmailVerification | None:
    return db.get(EmailVerification, normalize_email(email))


def is_email_verified(db: Session, email: str) -> bool:
    record = get_verification_record(db, email)
    return bool(record and record.verified_at is not None)


def issue_verification_token(db: Session, email: str) -> str:
    normalized_email = normalize_email(email)
    record = db.get(EmailVerification, normalized_email)
    if record is None:
        record = EmailVerification(email=normalized_email)
        db.add(record)

    token = secrets.token_urlsafe(32)
    record.token = token
    record.expires_at = _utcnow() + timedelta(hours=24)
    record.verified_at = None
    db.commit()
    return token


def mark_email_verified(db: Session, token: str) -> str | None:
    record = db.query(EmailVerification).filter(EmailVerification.token == token).first()
    if not record or not record.expires_at or record.expires_at < _utcnow():
        return None

    record.verified_at = _utcnow()
    record.token = None
    record.expires_at = None
    db.commit()
    return record.email


async def send_verification_email(email: str, token: str) -> None:
    if not settings.SENDGRID_API_KEY:
        print(
            f"[verification-email] SendGrid not configured. Verification URL: "
            f"{settings.FRONTEND_URL}/?verify_token={token}"
        )
        return

    import httpx

    verify_url = f"{settings.FRONTEND_URL}/?verify_token={token}"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": settings.FROM_EMAIL, "name": "VAREX AI Interview"},
                "subject": "Verify your email to continue with VAREX interviews",
                "content": [{
                    "type": "text/html",
                    "value": f"""
                    <div style=\"font-family:sans-serif;max-width:600px;margin:0 auto\">
                      <h2>Verify your email</h2>
                      <p>Your first mock interview is unlocked. To continue with additional interviews, verify your email address.</p>
                      <a href=\"{verify_url}\" style=\"background:#0ea5e9;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;margin:16px 0;font-weight:600\">
                        Verify Email
                      </a>
                      <p style=\"color:#888;font-size:13px\">This link is valid for 24 hours.</p>
                    </div>
                    """,
                }],
            },
        )
