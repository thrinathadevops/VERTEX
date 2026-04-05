import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _build_claims(subject: str, expire: datetime, token_type: str, extra_claims: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": token_type,
    }
    if extra_claims:
        payload.update(extra_claims)
    return payload


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = _build_claims(subject, expire, "access", extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_claims(subject, expire, "refresh", extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require_sub": True, "require_exp": True},
        )
    except JWTError:
        return None
