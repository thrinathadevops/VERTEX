"""
app/api/v1/haproxy.py
=====================
FastAPI router for the HAProxy tuning calculator.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.haproxy import HAProxyInput, HAProxyOutput
from app.calculators.haproxy_calculator import HAProxyCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=HAProxyOutput,
    summary="HAProxy – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — maxconn, threading, timeouts, health checks, SSL termination.
**EXISTING mode** — audit current haproxy.cfg and identify misconfigurations.
    """,
)
def calculate_haproxy(inp: HAProxyInput) -> HAProxyOutput:
    try:
        result = HAProxyCalculator(inp).generate()
        logger.info(
            "HAProxy calculate",
            extra={"mode": inp.mode.value, "ram_gb": inp.ram_gb,
                   "maxconn": result.global_maxconn},
        )
        return result
    except ValueError as e:
        logger.warning("HAProxy validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/example/new", summary="HAProxy – Example NEW mode request")
def haproxy_example_new() -> JSONResponse:
    return JSONResponse({
        "mode": "new", "cpu_cores": 4, "ram_gb": 8, "os_type": "ubuntu-22",
        "expected_concurrent": 10000, "backend_count": 4,
        "ssl_enabled": True, "http_mode": "http",
    })


@router.post("/example/existing", summary="HAProxy – Example EXISTING mode audit")
def haproxy_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode": "existing", "cpu_cores": 4, "ram_gb": 8, "os_type": "rhel-9",
        "expected_concurrent": 10000, "backend_count": 4,
        "ssl_enabled": True, "http_mode": "http",
        "existing": {
            "global_maxconn": 2000, "frontend_maxconn": 1000, "nbthread": 1,
            "timeout_connect": "5s", "timeout_client": "50s", "timeout_server": "50s",
            "ssl_enabled": False, "stats_enabled": False, "haproxy_version": "2.8.5",
            "os_sysctl": {"net.core.somaxconn": "128"},
        },
    })
