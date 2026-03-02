import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import nginx, redis, tomcat
from app.core.config import settings
from app.core.exceptions import unhandled_exception_handler, validation_exception_handler
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(nginx.router,  prefix="/api/v1/nginx",  tags=["NGINX"])
app.include_router(redis.router,  prefix="/api/v1/redis",  tags=["Redis"])
app.include_router(tomcat.router, prefix="/api/v1/tomcat", tags=["Tomcat"])


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "version": settings.APP_VERSION}
