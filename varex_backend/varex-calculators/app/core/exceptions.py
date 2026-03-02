import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Validation error on %s: %s", request.url.path, str(exc))
    return JSONResponse(status_code=422, content={"detail": str(exc)})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s", request.url.path, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
