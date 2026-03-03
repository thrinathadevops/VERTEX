"""
app/api/v1/httpd.py
===================
FastAPI router for the Apache HTTPD tuning calculator.

Endpoints
---------
POST /api/v1/httpd/calculate
    mode=new      → generate httpd.conf from hardware + workload specs
    mode=existing → audit current HTTPD config and return safe upgrade plan

POST /api/v1/httpd/example/new
    Returns a pre-filled example NEW mode request body (event MPM)

POST /api/v1/httpd/example/existing
    Returns a pre-filled EXISTING mode body with common misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.varex_calculators.schemas.httpd import HttpdInput, HttpdOutput
from app.varex_calculators.calculators.httpd_calculator import HttpdCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=HttpdOutput,
    summary="Apache HTTPD – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- `MaxRequestWorkers` calculated per MPM type:
  - **event/worker**: `max(expected_concurrent, cpu_cores × 2 × ThreadsPerChild)`
  - **prefork**: `floor(RAM × 70% / 10MB_per_proc)`, capped at 1024
- `ServerLimit` calculated as `ceil(MRW / TPC) + 4`
- Complete `httpd.conf` snippet with MPM block, SSL, proxy, static, security headers
- 25+ tiered params with deep explanations
- OS sysctl block

**EXISTING mode** — audit your current `httpd.conf`:
- Detects `ServerLimit × ThreadsPerChild < MaxRequestWorkers` silent truncation
- Flags `KeepAlive=Off` (full TLS re-handshake per request), `ServerTokens=Full`, high Timeout
- `current_value` on every param vs VAREX recommendation

**MPM selection guide:**
- `event` → default for modern Apache 2.4, handles keep-alive via listener thread (C10K capable)
- `worker` → thread-based, no dedicated keep-alive listener
- `prefork` → required for mod_php / non-thread-safe modules (RAM-limited to ~1024 processes)
    """,
)
def calculate_httpd(inp: HttpdInput) -> HttpdOutput:
    """
    Calculate optimal Apache HTTPD configuration.

    Raises 422 for invalid inputs.
    Raises 500 for unexpected calculation errors.
    """
    try:
        result = HttpdCalculator(inp).generate()
        logger.info(
            "HTTPD calculate",
            extra={
                "mode":                inp.mode.value,
                "mpm":                 inp.mpm,
                "cpu_cores":           inp.cpu_cores,
                "ram_gb":              inp.ram_gb,
                "max_request_workers": result.max_request_workers,
                "server_limit":        result.server_limit,
                "threads_per_child":   result.threads_per_child,
                "audit_count":         len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("HTTPD validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="Apache HTTPD – Example NEW mode request (event MPM)",
    include_in_schema=True,
)
def httpd_example_new() -> JSONResponse:
    """Returns a sample NEW mode request — copy-paste into /calculate."""
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          8,
        "ram_gb":             32,
        "os_type":            "ubuntu-22",
        "expected_concurrent":2000,
        "avg_request_ms":     150,
        "mpm":                "event",
        "ssl_enabled":        True,
        "reverse_proxy":      True,
        "serve_static":       True,
    })


@router.post(
    "/example/existing",
    summary="Apache HTTPD – Example EXISTING mode audit (with common misconfigs)",
    include_in_schema=True,
)
def httpd_example_existing() -> JSONResponse:
    """
    Returns EXISTING mode body with intentional misconfigs:
    - MaxRequestWorkers=150 (default Apache install — far too low)
    - ServerLimit=150 + ThreadsPerChild=25 → silent cap at 150×25=3750
      but MaxRequestWorkers=150 → actually limited correctly here, BUT
      if someone sets MRW=1000 with SL=150 and TPC=25 → SL×TPC=3750 ok
    - KeepAlive=Off (full TLS handshake every request)
    - KeepAliveTimeout=300s (workers held 5 minutes by idle connections)
    - Timeout=300s (default — workers blocked 5 minutes on slow clients)
    - ServerTokens=Full (exposes Apache version)
    - net.core.somaxconn=128 (OS accept queue starved)
    """
    return JSONResponse({
        "mode":               "existing",
        "cpu_cores":          4,
        "ram_gb":             16,
        "os_type":            "rhel-8",
        "expected_concurrent":500,
        "avg_request_ms":     200,
        "mpm":                "prefork",
        "ssl_enabled":        True,
        "reverse_proxy":      False,
        "serve_static":       True,
        "existing": {
            "max_request_workers":       150,
            "server_limit":              150,
            "threads_per_child":         25,
            "min_spare_threads":         5,
            "max_spare_threads":         10,
            "keep_alive":                "Off",
            "keep_alive_timeout":        300,
            "max_keep_alive_requests":   100,
            "timeout":                   300,
            "server_tokens":             "Full",
            "mpm_model":                 "prefork",
            "apache_version":            "2.4.51",
            "os_sysctl": {
                "net.core.somaxconn":  "128",
                "vm.swappiness":       "60",
                "fs.file-max":         "65536",
            },
        },
    })


