# PATH: varex_backend/app/main.py
# FIX: All include_router() calls moved to AFTER app = FastAPI()
# FIX: Removed Base.metadata.create_all (use alembic only)
# FIX: analytics router now registered
# FIX: subscriptions uses subscriptions.py (not subscription.py)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import structured_logger
from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()    # Start APScheduler on startup
    yield
    stop_scheduler()     # Graceful shutdown


app = FastAPI(
    title="VAREX Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# ── CORS (must be LAST added so it runs FIRST on requests) ───────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
from app.api.v1 import (
    auth,
    users,
    content,
    subscriptions,   # uses subscriptions.py (full version)
    leads,
    workshops,
    portfolio,
    team,
    certifications,
    faq,
    analytics,
    webhooks,
)
from app.ai_interview.api.v1 import interview as ai_interview

API_V1 = "/api/v1"

app.include_router(auth.router,           prefix=f"{API_V1}/auth",          tags=["Auth"])
app.include_router(users.router,          prefix=f"{API_V1}/users",         tags=["Users"])
app.include_router(content.router,        prefix=f"{API_V1}/content",       tags=["Content"])
app.include_router(subscriptions.router,  prefix=f"{API_V1}/subscriptions", tags=["Subscriptions"])
app.include_router(leads.router,          prefix=f"{API_V1}/leads",         tags=["Leads"])
app.include_router(workshops.router,      prefix=f"{API_V1}/workshops",     tags=["Workshops"])
app.include_router(portfolio.router,      prefix=f"{API_V1}/portfolio",     tags=["Portfolio"])
app.include_router(team.router,           prefix=f"{API_V1}/team",          tags=["Team"])
app.include_router(certifications.router, prefix=f"{API_V1}/certifications",tags=["Certifications"])
app.include_router(faq.router,            prefix=f"{API_V1}/faq",           tags=["FAQ"])
app.include_router(analytics.router,      prefix=f"{API_V1}/analytics",     tags=["Analytics"])
app.include_router(ai_interview.router,   prefix=f"{API_V1}/interview",     tags=["Interview"])
app.include_router(webhooks.router,       prefix=f"{API_V1}/webhooks",      tags=["Webhooks"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    structured_logger.error(f"Unhandled error: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again later."})


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
