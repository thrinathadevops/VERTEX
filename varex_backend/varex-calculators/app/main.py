from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exceptions import validation_exception_handler, unhandled_exception_handler

# ── import all routers ──────────────────────────────────────────────────────
from app.api.v1 import nginx, redis, tomcat, httpd, ohs, ihs, iis, podman, kubernetes, os_linux

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("VAREX started", extra={"version": settings.APP_VERSION})
    yield
    logger.info("VAREX shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade tuning calculator for NGINX, Redis, Tomcat, Apache HTTPD, "
        "Oracle HTTP Server (OHS), IBM HTTP Server (IHS), IIS, Podman, Kubernetes, "
        "and Linux OS kernel parameters.\n\n"
        "**Two modes per endpoint:**\n"
        "- `mode=new` — Generate a fresh, formula-driven config from hardware specs\n"
        "- `mode=existing` — Audit your current settings and get a safe upgrade plan\n\n"
        "**Every parameter includes:**\n"
        "- `impact`: MAJOR / MEDIUM / MINOR\n"
        "- `reason`: deep formula-based explanation (not just docs copy-paste)\n"
        "- `command`: ready-to-run sysctl / config snippet\n"
        "- `current_value`: what you have now (existing mode)\n"
        "- `safe_to_apply_live`: whether a rolling apply is safe without restart"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# ── exception handlers ──────────────────────────────────────────────────────
app.add_exception_handler(ValueError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Prometheus metrics ──────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ── routers ─────────────────────────────────────────────────────────────────
API = "/api/v1"
app.include_router(nginx.router,      prefix=f"{API}/nginx",      tags=["NGINX"])
app.include_router(redis.router,      prefix=f"{API}/redis",      tags=["Redis"])
app.include_router(tomcat.router,     prefix=f"{API}/tomcat",     tags=["Tomcat"])
app.include_router(httpd.router,      prefix=f"{API}/httpd",      tags=["Apache HTTPD"])
app.include_router(ohs.router,        prefix=f"{API}/ohs",        tags=["Oracle HTTP Server"])
app.include_router(ihs.router,        prefix=f"{API}/ihs",        tags=["IBM HTTP Server"])
app.include_router(iis.router,        prefix=f"{API}/iis",        tags=["IIS"])
app.include_router(podman.router,     prefix=f"{API}/podman",     tags=["Podman"])
app.include_router(kubernetes.router, prefix=f"{API}/kubernetes", tags=["Kubernetes"])
app.include_router(os_linux.router,   prefix=f"{API}/os",         tags=["Linux OS"])


# ── health & info endpoints ──────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "metrics": "/metrics",
        "endpoints": {
            "nginx":      f"{API}/nginx/calculate",
            "redis":      f"{API}/redis/calculate",
            "tomcat":     f"{API}/tomcat/calculate",
            "httpd":      f"{API}/httpd/calculate",
            "ohs":        f"{API}/ohs/calculate",
            "ihs":        f"{API}/ihs/calculate",
            "iis":        f"{API}/iis/calculate",
            "podman":     f"{API}/podman/calculate",
            "kubernetes": f"{API}/kubernetes/calculate",
            "os_linux":   f"{API}/os/calculate",
        },
    }
