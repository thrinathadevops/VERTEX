import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches ValueError raised by calculators (e.g. invalid param combinations)
    and returns a clean 422 JSON response instead of a 500.
    """
    logger.warning(
        "Validation error",
        extra={"path": str(request.url.path), "detail": str(exc)},
    )
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "path": str(request.url.path)},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unhandled exceptions, logs with full traceback,
    returns 500 without leaking internal stack traces to clients.
    """
    logger.error(
        "Unhandled exception",
        extra={"path": str(request.url.path)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
