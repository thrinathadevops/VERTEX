import logging
import sys

from pythonjsonlogger import jsonlogger
from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structured JSON logging for all application loggers.
    Format: timestamp | logger | level | message + any extra fields.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "uvicorn.error", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
