"""
app/api/v1/tomcat.py
====================
FastAPI router for the Tomcat tuning calculator.

Endpoints
---------
POST /api/v1/tomcat/calculate
    mode=new      → generate server.xml + CATALINA_OPTS from hardware + workload
    mode=existing → audit current Tomcat/JVM settings and return safe upgrade plan

POST /api/v1/tomcat/example/new
    Returns a pre-filled NEW mode request body

POST /api/v1/tomcat/example/existing
    Returns a pre-filled EXISTING mode body with common misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.varex_calculators.schemas.tomcat import TomcatInput, TomcatOutput
from app.varex_calculators.calculators.tomcat_calculator import TomcatCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=TomcatOutput,
    summary="Tomcat – Calculate optimal server.xml + JVM config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- `maxThreads` calculated via **Goetz formula**: N = U × C × (1 + W/C_time)
- `goetz_formula_trace`: full step-by-step working of the thread formula
- Complete `server.xml` Connector snippet
- Ready-to-paste `CATALINA_OPTS` with GC flags for G1GC/ZGC/Shenandoah/ParallelGC
- 25+ tiered params (MAJOR/MEDIUM/MINOR) with formula-backed explanations
- OS sysctl block (THP disabled — mandatory for JVM)

**EXISTING mode** — audit current `server.xml` + JVM flags:
- Flags low maxThreads, Xms≠Xmx heap resize pauses, ParallelGC on web workloads
- Detects undersized Metaspace, BIO connector (HTTP/1.1), compression=off
- `current_value` on every param vs VAREX recommendation

**Goetz formula:**  
`N = U × C × (1 + io_wait_ratio / (1 - io_wait_ratio))`  
Where U=0.90 (target CPU util), C=cpu_cores, io_wait_ratio = I/O fraction of request time.
    """,
)
def calculate_tomcat(inp: TomcatInput) -> TomcatOutput:
    """
    Calculate optimal Tomcat configuration.

    Raises 422 for invalid input combinations.
    Raises 500 for unexpected calculation errors.
    """
    try:
        result = TomcatCalculator(inp).generate()
        logger.info(
            "Tomcat calculate",
            extra={
                "mode":         inp.mode.value,
                "cpu_cores":    inp.cpu_cores,
                "ram_gb":       inp.ram_gb,
                "max_threads":  result.max_threads,
                "xmx_gb":       result.xmx_gb,
                "gc_type":      inp.gc_type,
                "java_version": inp.java_version,
                "audit_count":  len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("Tomcat validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="Tomcat – Example NEW mode request",
    include_in_schema=True,
)
def tomcat_example_new() -> JSONResponse:
    """Returns a sample NEW mode request body — copy-paste into /calculate."""
    return JSONResponse({
        "mode":               "new",
        "cpu_cores":          8,
        "ram_gb":             32,
        "os_type":            "ubuntu-22",
        "heap_ratio":         0.50,
        "target_concurrency": 500,
        "avg_response_ms":    200,
        "io_wait_ratio":      0.80,
        "connector_type":     "NIO",
        "ssl_enabled":        False,
        "compression_enabled":True,
        "gc_type":            "G1GC",
        "java_version":       17,
    })


@router.post(
    "/example/existing",
    summary="Tomcat – Example EXISTING mode audit (with common misconfigs)",
    include_in_schema=True,
)
def tomcat_example_existing() -> JSONResponse:
    """
    Returns EXISTING mode body with intentional misconfigs:
    - maxThreads=150 (BIO-era default, too low for NIO)
    - Xms=1g ≠ Xmx=2g (heap resize pauses on load)
    - GC=ParallelGC (stop-the-world pauses on web workload)
    - MetaspaceSize=128MB (too small for Spring Boot)
    - connector=HTTP/1.1 (BIO blocking I/O)
    - compression=off
    - transparent_hugepage=always (JVM latency spikes)
    - somaxconn=128 (OS accept queue starved)
    """
    return JSONResponse({
        "mode":               "existing",
        "cpu_cores":          4,
        "ram_gb":             16,
        "os_type":            "rhel-8",
        "heap_ratio":         0.50,
        "target_concurrency": 200,
        "avg_response_ms":    300,
        "io_wait_ratio":      0.80,
        "connector_type":     "NIO",
        "ssl_enabled":        False,
        "compression_enabled":True,
        "gc_type":            "G1GC",
        "java_version":       11,
        "existing": {
            "max_threads":         150,
            "min_spare_threads":   4,
            "accept_count":        100,
            "connection_timeout":  60000,
            "xms_gb":              1.0,
            "xmx_gb":              2.0,
            "gc_type":             "ParallelGC",
            "metaspace_mb":        128,
            "connector_protocol":  "HTTP/1.1",
            "compression":         "off",
            "tomcat_version":      "9.0.83",
            "os_sysctl": {
                "net.core.somaxconn":   "128",
                "vm.swappiness":        "60",
                "transparent_hugepage": "always",
            },
        },
    })


