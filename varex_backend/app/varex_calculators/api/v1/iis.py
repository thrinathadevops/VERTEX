"""
app/api/v1/iis.py
=================
FastAPI router for the IIS tuning calculator.

Endpoints
---------
POST /api/v1/iis/calculate
    mode=new      → generate applicationHost.config + PowerShell + Windows tuning
    mode=existing → audit current IIS settings and return safe upgrade plan

POST /api/v1/iis/example/new-aspnetcore
    Returns a pre-filled NEW mode request (ASP.NET Core / net8.0)

POST /api/v1/iis/example/new-aspnetfx
    Returns a pre-filled NEW mode request (ASP.NET Framework 4.x, web garden)

POST /api/v1/iis/example/existing
    Returns a pre-filled EXISTING mode body with common IIS misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.varex_calculators.schemas.iis import IISInput, IISOutput
from app.varex_calculators.calculators.iis_calculator import IISCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=IISOutput,
    summary="IIS – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- `maxWorkerThreads` = `cpu_cores × 100` (CLR thread pool)
- `maxIoThreads` = `cpu_cores × 100` (IOCP completions)
- App Pool request queue = `max(expected_concurrent × 2, 5000)`
- http.sys kernel queue = `max(expected_concurrent × 4, 10000)`
- Private memory limit = `(RAM × 80% / app_pools) × 70%` in KB
- Complete `applicationHost.config` XML snippet
- Complete PowerShell `WebAdministration` command block
- Windows registry + `netsh` tuning block (TCP, SCHANNEL, ephemeral ports, TlsTimedWaitDelay)

**EXISTING mode** — audit your current IIS config:
- Detects `maxWorkerThreads=25` (IIS install default — thread starvation)
- Flags `managedPipelineMode=Classic` (legacy ISAPI — 30% slower)
- `idleTimeout=20min` causing cold starts in production
- `headerWaitTimeout=120s` (Slowloris attack surface)
- `kernel_queue_length=1000` (http.sys default, silently drops at 1001)
- Deprecated TLS 1.0/1.1 in SCHANNEL

**IIS-specific dual outputs:**
- `apphostconfig_snippet`: XML for `applicationHost.config`
- `powershell_snippet`: `WebAdministration` PowerShell commands (same settings)
- `os_sysctl_conf`: Windows `netsh` + registry tuning block
    """,
)
def calculate_iis(inp: IISInput) -> IISOutput:
    try:
        result = IISCalculator(inp).generate()
        logger.info(
            "IIS calculate",
            extra={
                "mode":               inp.mode.value,
                "cpu_cores":          inp.cpu_cores,
                "ram_gb":             inp.ram_gb,
                "dotnet_version":     inp.dotnet_version,
                "pipeline_mode":      inp.managed_pipeline_mode,
                "web_garden":         inp.web_garden,
                "max_worker_threads": result.max_worker_threads,
                "queue_length":       result.queue_length,
                "kernel_queue":       result.kernel_queue_length,
                "priv_mem_kb":        result.private_memory_limit_kb,
                "audit_count":        len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("IIS validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new-aspnetcore",
    summary="IIS – Example NEW mode (ASP.NET Core / net8.0)",
    include_in_schema=True,
)
def iis_example_new_core() -> JSONResponse:
    return JSONResponse({
        "mode":                  "new",
        "cpu_cores":             8,
        "ram_gb":                32,
        "os_type":               "windows-server-2022",
        "expected_concurrent":   1000,
        "avg_request_ms":        150,
        "app_pool_count":        1,
        "web_garden":            False,
        "dotnet_version":        "net8.0",
        "managed_pipeline_mode": "Integrated",
        "ssl_enabled":           True,
        "http2_enabled":         True,
        "output_cache_enabled":  True,
        "reverse_proxy":         False,
    })


@router.post(
    "/example/new-aspnetfx",
    summary="IIS – Example NEW mode (ASP.NET Framework 4.x, web garden)",
    include_in_schema=True,
)
def iis_example_new_fx() -> JSONResponse:
    return JSONResponse({
        "mode":                  "new",
        "cpu_cores":             8,
        "ram_gb":                32,
        "os_type":               "windows-server-2022",
        "expected_concurrent":   500,
        "avg_request_ms":        300,
        "app_pool_count":        2,
        "web_garden":            True,
        "dotnet_version":        "v4.0",
        "managed_pipeline_mode": "Integrated",
        "ssl_enabled":           True,
        "http2_enabled":         True,
        "output_cache_enabled":  True,
        "reverse_proxy":         False,
    })


@router.post(
    "/example/existing",
    summary="IIS – Example EXISTING mode audit (with common IIS misconfigs)",
    include_in_schema=True,
)
def iis_example_existing() -> JSONResponse:
    """
    Intentional IIS misconfigs:
    - maxWorkerThreads=25, maxIoThreads=25 (IIS install defaults — thread starvation)
    - queue_length=1000, kernel_queue_length=1000 (default — drops at 1001)
    - managedPipelineMode=Classic (30% slower than Integrated)
    - idleTimeout=20 (cold start every 20min idle)
    - connectionTimeout=120s, headerWaitTimeout=120s (Slowloris exposure)
    - output_cache_enabled=False (missed performance opportunity)
    - TLS 1.0 + 1.1 still enabled in SCHANNEL
    - http2_enabled=False
    """
    return JSONResponse({
        "mode":                  "existing",
        "cpu_cores":             4,
        "ram_gb":                16,
        "os_type":               "windows-server-2019",
        "expected_concurrent":   500,
        "avg_request_ms":        200,
        "app_pool_count":        1,
        "web_garden":            False,
        "dotnet_version":        "v4.0",
        "managed_pipeline_mode": "Classic",
        "ssl_enabled":           True,
        "http2_enabled":         False,
        "output_cache_enabled":  False,
        "reverse_proxy":         False,
        "existing": {
            "max_processes":           1,
            "queue_length":            1000,
            "rapid_fail_protection":   True,
            "recycle_minutes":         1740,
            "recycle_requests":        0,
            "idle_timeout":            20,
            "max_worker_threads":      25,
            "max_io_threads":          25,
            "max_connections":         0,
            "connection_timeout":      120,
            "header_wait_timeout":     120,
            "kernel_queue_length":     1000,
            "tls_protocols":           "TLS 1.0, TLS 1.1, TLS 1.2",
            "iis_version":             "10.0",
            "output_cache_enabled":    False,
            "dotnet_version":          "v4.0",
            "managed_pipeline_mode":   "Classic",
        },
    })


