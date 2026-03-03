"""
app/api/v1/ohs.py
=================
FastAPI router for the Oracle HTTP Server (OHS) tuning calculator.

Endpoints
---------
POST /api/v1/ohs/calculate
    mode=new      → generate OHS config from hardware + workload
    mode=existing → audit current OHS settings and return safe upgrade plan

POST /api/v1/ohs/example/new
    Returns a pre-filled NEW mode request body (WebLogic proxy)

POST /api/v1/ohs/example/new-fusion
    Returns a pre-filled NEW mode request body (Fusion Apps optimised)

POST /api/v1/ohs/example/existing
    Returns a pre-filled EXISTING mode audit body with common OHS misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.ohs import OHSInput, OHSOutput
from app.calculators.ohs_calculator import OHSCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=OHSOutput,
    summary="OHS – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- `MaxRequestWorkers` = `max(expected_concurrent, cpu_cores × 2 × 25)`
- `ServerLimit` = `ceil(MRW / TPC) + 4`
- Complete OHS conf snippet with MPM, mod_wl_ohs, SSL (Oracle Wallet), Fusion App headers
- `WLIOTimeout` = `avg_request_ms × 3`, clamped to [30s, 600s]
- 25+ tiered params with OHS/FMW-specific explanations
- OS sysctl block for Oracle Linux / RHEL

**EXISTING mode** — audit current OHS config:
- Detects OHS default `MaxRequestWorkers=150` (install default, production-unsafe)
- Flags `KeepAlive=Off` (OHS default — full TLS handshake on every request)
- Silent `ServerLimit × TPC < MaxRequestWorkers` truncation detection
- Deprecated TLS 1.0/1.1 in SSLProtocol
- Excessive WLIOTimeout holding threads on hung WLS

**OHS-specific params:**
- `backend_type=fusion`: enlarges `LimitRequestFieldSize` to 32768 for SAML/OAM tokens,
  adds `LimitRequestFields=200`, enables `RLimitMEM/CPU`
- `backend_type=weblogic`: generates full `mod_wl_ohs` block with failover config
- Oracle Wallet SSL (not PEM): `SSLWallet` path with `orapki` usage instructions
    """,
)
def calculate_ohs(inp: OHSInput) -> OHSOutput:
    """
    Calculate optimal Oracle HTTP Server configuration.

    Raises 422 for invalid inputs.
    Raises 500 for unexpected calculation errors.
    """
    try:
        result = OHSCalculator(inp).generate()
        logger.info(
            "OHS calculate",
            extra={
                "mode":                inp.mode.value,
                "mpm":                 inp.mpm,
                "cpu_cores":           inp.cpu_cores,
                "ram_gb":              inp.ram_gb,
                "backend_type":        inp.backend_type,
                "fusion_apps":         inp.fusion_apps,
                "wls_cluster_size":    inp.wls_cluster_size,
                "max_request_workers": result.max_request_workers,
                "server_limit":        result.server_limit,
                "audit_count":         len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("OHS validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="OHS – Example NEW mode (WebLogic proxy)",
    include_in_schema=True,
)
def ohs_example_new() -> JSONResponse:
    """Sample NEW mode request — WebLogic cluster proxy, SSL, event MPM."""
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          8,
        "ram_gb":             32,
        "os_type":            "rhel-9",
        "expected_concurrent":1000,
        "avg_request_ms":     250,
        "mpm":                "event",
        "backend_type":       "weblogic",
        "ssl_enabled":        True,
        "fusion_apps":        False,
        "wls_cluster_size":   3,
    })


@router.post(
    "/example/new-fusion",
    summary="OHS – Example NEW mode (Fusion Apps)",
    include_in_schema=True,
)
def ohs_example_new_fusion() -> JSONResponse:
    """
    Sample NEW mode for Oracle Fusion Apps:
    - fusion_apps=True → LimitRequestFieldSize=32768 for SAML/OAM tokens
    - avg_request_ms=500 → WLIOTimeout=1500ms (× 3)
    - Large RAM/cores for ADF-heavy concurrent sessions
    """
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          16,
        "ram_gb":             64,
        "os_type":            "rhel-9",
        "expected_concurrent":2000,
        "avg_request_ms":     500,
        "mpm":                "event",
        "backend_type":       "fusion",
        "ssl_enabled":        True,
        "fusion_apps":        True,
        "wls_cluster_size":   4,
    })


@router.post(
    "/example/existing",
    summary="OHS – Example EXISTING mode audit (with common misconfigs)",
    include_in_schema=True,
)
def ohs_example_existing() -> JSONResponse:
    """
    EXISTING mode audit body with OHS-specific misconfigs:
    - MaxRequestWorkers=150 (OHS install default — production-unsafe)
    - ServerLimit=6 × ThreadsPerChild=25 = 150 cap (matches MRW but grossly low)
    - KeepAlive=Off (OHS default — TLS re-handshake every request)
    - KeepAliveTimeout=300s (workers held 5 min by idle connections)
    - Timeout=300s (default — workers blocked 5 min on slow clients)
    - WLIOTimeout=300000ms (5 min — hung WLS holds OHS threads too long)
    - WLConnectTimeout=10ms (too low — premature WLS failover)
    - ServerTokens=Full (exposes OHS/Apache version)
    - TLSv1.0 still active in SSLProtocol
    - net.core.somaxconn=128 (OS accept queue starved)
    """
    return JSONResponse({
        "mode":               "existing",
        "cpu_cores":          4,
        "ram_gb":             16,
        "os_type":            "rhel-8",
        "expected_concurrent":500,
        "avg_request_ms":     300,
        "mpm":                "worker",
        "backend_type":       "weblogic",
        "ssl_enabled":        True,
        "fusion_apps":        False,
        "wls_cluster_size":   2,
        "existing": {
            "max_request_workers":       150,
            "server_limit":              6,
            "threads_per_child":         25,
            "keep_alive":                "Off",
            "keep_alive_timeout":        300,
            "timeout":                   300,
            "server_tokens":             "Full",
            "mpm_model":                 "worker",
            "wl_connect_timeout":        10,
            "wl_io_timeout":             300000,
            "ssl_protocols":             "TLSv1 TLSv1.1 TLSv1.2",
            "ohs_version":               "12.2.1.4.0",
            "os_sysctl": {
                "net.core.somaxconn": "128",
                "vm.swappiness":      "60",
            },
        },
    })
