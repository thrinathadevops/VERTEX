"""
app/api/v1/nginx.py
===================
FastAPI router for the NGINX tuning calculator.

Endpoints
---------
POST /api/v1/nginx/calculate
    mode=new      → generate fresh NGINX config from hardware + workload specs
    mode=existing → audit current nginx.conf and return safe upgrade plan

POST /api/v1/nginx/example/new
    Returns a pre-filled example NEW mode request body

POST /api/v1/nginx/example/existing
    Returns a pre-filled example EXISTING mode audit request body
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.varex_calculators.schemas.nginx import NginxInput, NginxOutput
from app.varex_calculators.calculators.nginx_calculator import NginxCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=NginxOutput,
    summary="NGINX – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, get a complete
`nginx.conf` snippet with every parameter explained (formula, impact, command).

**EXISTING mode** — additionally supply your current `nginx.conf` values
in the `existing` block. The response includes:
- `audit_findings`: list of MAJOR/MEDIUM issues found in your current config
- `current_value` on every param: what you have now vs what VAREX recommends
- `safe_to_apply_live`: whether the change needs an nginx reload or full restart

**OS sysctl** — pass `existing.os_sysctl` with your current kernel values
for a full OS-level audit alongside the NGINX tuning.
    """,
)
def calculate_nginx(inp: NginxInput) -> NginxOutput:
    """
    Calculate optimal NGINX configuration.

    Raises 422 for invalid input combinations (e.g. negative RAM).
    Raises 500 for unexpected calculation errors.
    """
    try:
        result = NginxCalculator(inp).generate()
        logger.info(
            "NGINX calculate",
            extra={
                "mode":       inp.mode.value,
                "cpu_cores":  inp.cpu_cores,
                "ram_gb":     inp.ram_gb,
                "wp":         result.worker_processes,
                "wc":         result.worker_connections,
                "max_clients":result.estimated_max_clients,
            },
        )
        return result
    except ValueError as e:
        logger.warning("NGINX validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="NGINX – Example NEW mode request",
    include_in_schema=True,
)
def nginx_example_new() -> JSONResponse:
    """Returns a sample NEW mode request body you can copy-paste into /calculate."""
    return JSONResponse({
        "mode":              "new",
        "cpu_cores":         8,
        "ram_gb":            32,
        "os_type":           "ubuntu-22",
        "expected_rps":      50000,
        "avg_response_kb":   8.0,
        "static_pct":        20,
        "keepalive_enabled": True,
        "ssl_enabled":       True,
        "reverse_proxy":     True,
    })


@router.post(
    "/example/existing",
    summary="NGINX – Example EXISTING mode audit request",
    include_in_schema=True,
)
def nginx_example_existing() -> JSONResponse:
    """Returns a sample EXISTING mode request body showing common misconfigurations."""
    return JSONResponse({
        "mode":              "existing",
        "cpu_cores":         4,
        "ram_gb":            16,
        "os_type":           "rhel-8",
        "expected_rps":      10000,
        "avg_response_kb":   4.0,
        "static_pct":        50,
        "keepalive_enabled": True,
        "ssl_enabled":       True,
        "reverse_proxy":     False,
        "existing": {
            "worker_processes":     2,
            "worker_connections":   512,
            "worker_rlimit_nofile": 1024,
            "keepalive_timeout":    300,
            "ssl_protocols":        "TLSv1 TLSv1.1 TLSv1.2",
            "ssl_buffer_size":      "16k",
            "server_tokens":        "on",
            "nginx_version":        "1.18.0",
            "os_sysctl": {
                "net.core.somaxconn":  "128",
                "vm.swappiness":       "60",
                "fs.file-max":         "65536",
            },
        },
    })


