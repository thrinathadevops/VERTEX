# PATH: varex_backend/app/core/config.py
# FIX 5.5: SECRET_KEY raises ValueError if default used in production
# FIX 5.10: ALLOWED_ORIGINS includes varextech.in (not just .com)

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "VAREX Platform"
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Security ─────────────────────────────────────────────────
    SECRET_KEY:                  str = "insecure-default-change-me"
    ALGORITHM:                   str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS:   int = 7

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://varex:varexpassword@localhost:5432/varexdb"

    # ── CORS ─────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://varextech.in",        # FIX 5.10 — was .com
        "https://www.varextech.in",
    ]

    # ── Razorpay ─────────────────────────────────────────────────
    RAZORPAY_KEY_ID:       str = ""
    RAZORPAY_KEY_SECRET:   str = ""    # FIX 2.1 — was RAZORPAY_SECRET in some places
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── AWS ──────────────────────────────────────────────────────
    AWS_REGION:            str = "ap-south-1"
    AWS_ACCESS_KEY_ID:     str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET:         str = "varex-assets"
    AWS_CLOUDFRONT_URL:    str = ""

    # ── Email ─────────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL:       str = "noreply@varextech.in"

    # ── Internal ──────────────────────────────────────────────────
    INTERNAL_API_SECRET: str = ""

    # ── Redis ─────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    
    
    # ── LLM (Google Gemini) ───────────────────────────────────────
    GEMINI_API_KEY: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and v == "insecure-default-change-me":
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in production. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
