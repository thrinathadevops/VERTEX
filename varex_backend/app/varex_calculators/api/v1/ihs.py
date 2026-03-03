"""
app/api/v1/ihs.py
=================
FastAPI router for the IBM HTTP Server (IHS) tuning calculator.

Endpoints
---------
POST /api/v1/ihs/calculate
    mode=new      → generate httpd.conf + plugin-cfg.xml from specs
    mode=existing → audit current IHS settings and return safe upgrade plan

POST /api/v1/ihs/example/new
    Returns a pre-filled NEW mode request body (WAS proxy)

POST /api/v1/ihs/example/new-liberty
    Returns a pre-filled NEW mode request body (Liberty proxy)

POST /api/v1/ihs/example/existing
    Returns a pre-filled EXISTING mode audit body with common IHS misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.varex_calculators.schemas.ihs import IHSInput, IHSOutput
from app.varex_calculators.calculators.ihs_calculator import IHSCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=IHSOutput,
    summary="IHS – Calculate optimal config + plugin-cfg.xml (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- `MaxRequestWorkers` = `max(expected_concurrent, cpu_cores × 2 × 25)`
- `ServerLimit` = `ceil(MRW / 25) + 4`
- Complete `httpd.conf` snippet with MPM, IBM GSKit SSL, WebSphere plugin loader
- Full `plugin-cfg.xml` `ServerCluster` block with all WAS/Liberty members
- Plugin `IOTimeout` = `avg_request_ms × 3 / 1000s`, clamped [30s, 600s]
- Plugin `MaxConnections` per member = `ceil(MRW / cluster_size) × 1.5`
- IBM GSKit SSL syntax (`SSLEnable`, `SSLProtocolDisable`, `.kdb` KeyFile)
- OS sysctl block for RHEL / Oracle Linux / AIX

**EXISTING mode** — audit your current IHS config + plugin-cfg.xml values:
- Detects `MaxRequestWorkers=150` (IHS install default)
- Flags `KeepAlive=Off` (IHS default — full SSL handshake every request)
- Silent `ServerLimit × TPC < MaxRequestWorkers` truncation detection
- Plugin `ConnectTimeout` too low (WAS GC pause triggers premature failover)
- Excessive `IOTimeout` holding IHS workers on hung WAS threads
- Deprecated TLS protocols in GSKit SSL config

**IHS-specific outputs:**
- `plugin_cfg_snippet`: complete `plugin-cfg.xml` `ServerCluster` block
  with all WAS/Liberty members, `ConnectTimeout`, `IOTimeout`, `MaxConnections`
- `plugin_connect_timeout`, `plugin_io_timeout`, `plugin_max_connections`
  as top-level calculated values
    """,
)
def calculate_ihs(inp: IHSInput) -> IHSOutput:
    try:
        result = IHSCalculator(inp).generate()
        logger.info(
            "IHS calculate",
            extra={
                "mode":                inp.mode.value,
                "mpm":                 inp.mpm,
                "cpu_cores":           inp.cpu_cores,
                "ram_gb":              inp.ram_gb,
                "backend_type":        inp.backend_type,
                "was_cluster_size":    inp.was_cluster_size,
                "max_request_workers": result.max_request_workers,
                "server_limit":        result.server_limit,
                "plugin_io_timeout":   result.plugin_io_timeout,
                "plugin_max_conns":    result.plugin_max_connections,
                "audit_count":         len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("IHS validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="IHS – Example NEW mode (WAS proxy)",
    include_in_schema=True,
)
def ihs_example_new() -> JSONResponse:
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          8,
        "ram_gb":             32,
        "os_type":            "rhel-9",
        "expected_concurrent":1000,
        "avg_request_ms":     300,
        "mpm":                "event",
        "backend_type":       "was",
        "ssl_enabled":        True,
        "was_cluster_size":   3,
        "was_cell_name":      "prodCell",
        "dmgr_host":          "dmgr.example.com",
    })


@router.post(
    "/example/new-liberty",
    summary="IHS – Example NEW mode (Liberty proxy)",
    include_in_schema=True,
)
def ihs_example_new_liberty() -> JSONResponse:
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          8,
        "ram_gb":             32,
        "os_type":            "rhel-9",
        "expected_concurrent":1500,
        "avg_request_ms":     200,
        "mpm":                "event",
        "backend_type":       "liberty",
        "ssl_enabled":        True,
        "was_cluster_size":   4,
        "was_cell_name":      "libertyCell",
        "dmgr_host":          "dmgr.example.com",
    })


@router.post(
    "/example/existing",
    summary="IHS – Example EXISTING mode audit (with common misconfigs)",
    include_in_schema=True,
)
def ihs_example_existing() -> JSONResponse:
    """
    Intentional misconfigs:
    - MaxRequestWorkers=150 (IHS install default)
    - ServerLimit=6 × TPC=25 = 150 (matches but both too low)
    - KeepAlive=Off (IHS default — SSL handshake every request)
    - KeepAliveTimeout=300s
    - Timeout=300s
    - plugin ConnectTimeout=5s (too low, WAS GC triggers failover)
    - plugin IOTimeout=300s (5 min — hung WAS holds IHS workers)
    - plugin MaxConnections=20 (too low for cluster)
    - TLSv1 still listed in ssl_protocol
    - somaxconn=128
    """
    return JSONResponse({
        "mode":               "existing",
        "cpu_cores":          4,
        "ram_gb":             16,
        "os_type":            "rhel-8",
        "expected_concurrent":500,
        "avg_request_ms":     300,
        "mpm":                "worker",
        "backend_type":       "was",
        "ssl_enabled":        True,
        "was_cluster_size":   2,
        "was_cell_name":      "myCell",
        "dmgr_host":          "dmgr.example.com",
        "existing": {
            "max_request_workers":       150,
            "server_limit":              6,
            "threads_per_child":         25,
            "keep_alive":                "Off",
            "keep_alive_timeout":        300,
            "timeout":                   300,
            "server_tokens":             "Full",
            "mpm_model":                 "worker",
            "plugin_connect_timeout":    5,
            "plugin_io_timeout":         300,
            "plugin_retry_interval":     60,
            "plugin_max_connections":    20,
            "plugin_load_balance":       "Round Robin",
            "ssl_protocol":              "TLSv1 TLSv1.1 TLSv1.2",
            "ihs_version":               "9.0.5.18",
            "os_sysctl": {
                "net.core.somaxconn": "128",
                "vm.swappiness":      "60",
            },
        },
    })


