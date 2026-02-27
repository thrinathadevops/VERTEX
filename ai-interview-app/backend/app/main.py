"""
VAREX AI Interview Platform — Main Application
─────────────────────────────────────────────────
Production-ready FastAPI application with:
  - JWT Authentication (role-based access)
  - AI-powered interview engine (7-phase flow)
  - Pricing & discount engine (B2C + B2B)
  - Real-time background evaluation
  - Anti-cheat detection
  - Enterprise dashboard
  - Admin analytics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routes.admin import router as admin_router
from .routes.auth import router as auth_router
from .routes.enterprise import router as enterprise_router
from .routes.health import router as health_router
from .routes.interview import router as interview_router


def _parse_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Interview Assessment Platform with real-time evaluation, anti-cheat detection, and enterprise analytics.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# ─── Register all routers ────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(enterprise_router)
app.include_router(admin_router)
