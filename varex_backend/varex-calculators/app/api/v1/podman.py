"""
app/api/v1/podman.py
====================
FastAPI router for the Podman container tuning calculator.

Endpoints
---------
POST /api/v1/podman/calculate
    mode=new      → generate podman run flags + Quadlet .container unit
    mode=existing → audit current container config

POST /api/v1/podman/example/new-web
    Pre-filled NEW mode — rootless web container

POST /api/v1/podman/example/new-database
    Pre-filled NEW mode — rootful database container (PostgreSQL/Redis)

POST /api/v1/podman/example/existing
    Pre-filled EXISTING mode with common Podman misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.podman import PodmanInput, PodmanOutput
from app.calculators.podman_calculator import PodmanCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=PodmanOutput,
    summary="Podman – Calculate optimal container resource limits (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide host + container specs, receive:
- `--memory` = `container_ram_gb × 1024` MB
- `--cpus` = `container_cpu_cores`, cpu-quota = `cpus × 100000μs`
- `--memory-swap` = `memory × 2` (or = `memory` for database/cache — disables swap)
- `--pids-limit` = `max(expected_pids × 2, 512)`
- `--ulimit nofile` = `65535` (web) or `1048576` (database/cache)
- `--shm-size` = `/dev/shm` (database: `container_ram × 25%` for PostgreSQL shared_buffers)
- `--oom-score-adj`: batch=+500, database=-500, cache=-300
- Complete `podman run` flag block with comments
- Complete systemd Quadlet `.container` unit (Podman 4.4+)
- Host OS sysctl block

**EXISTING mode** — audit your current container run flags:
- Detects missing `--memory` (container can OOM the host)
- Flags `--pids-limit=-1` (fork bomb possible)
- `ulimit nofile=1024` (default — 513th connection fails)
- Missing `--security-opt=no-new-privileges`
- Missing `--cap-drop=ALL`
- Database container with swap enabled (1000× latency spike risk)
- rootful container where rootless is possible

**Container-type-specific tuning:**
- `web`: `nofile=65535`, `oom=0`, `drop_caps=NET_BIND_SERVICE`
- `database`: `nofile=1048576`, `oom=-500`, `swap=memory` (no swap), `shm=25% RAM`, `IPC_LOCK`
- `cache`: `nofile=1048576`, `oom=-300`, `swap=memory`
- `batch`: `oom=+500` (killed first under pressure)
    """,
)
def calculate_podman(inp: PodmanInput) -> PodmanOutput:
    try:
        result = PodmanCalculator(inp).generate()
        logger.info(
            "Podman calculate",
            extra={
                "mode":            inp.mode.value,
                "container_type":  inp.container_type,
                "cpu_cores":       inp.container_cpu_cores,
                "ram_gb":          inp.container_ram_gb,
                "rootless":        inp.rootless,
                "cgroup_version":  inp.cgroup_version,
                "use_quadlet":     inp.use_quadlet,
                "memory_mb":       result.memory_limit_mb,
                "pids_limit":      result.pids_limit,
                "audit_count":     len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("Podman validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new-web",
    summary="Podman – Example NEW mode (rootless web container)",
    include_in_schema=True,
)
def podman_example_new_web() -> JSONResponse:
    return JSONResponse({
        "mode":               "new",
        "host_cpu_cores":     8,
        "host_ram_gb":        32,
        "os_type":            "rhel-9",
        "container_cpu_cores":2.0,
        "container_ram_gb":   4.0,
        "container_type":     "web",
        "rootless":           True,
        "cgroup_version":     "v2",
        "use_quadlet":        True,
        "network_mode":       "bridge",
        "expected_pids":      512,
        "shm_size_mb":        64,
        "read_only_rootfs":   True,
        "drop_all_caps":      True,
    })


@router.post(
    "/example/new-database",
    summary="Podman – Example NEW mode (database container — PostgreSQL/Redis)",
    include_in_schema=True,
)
def podman_example_new_database() -> JSONResponse:
    """
    Database container specifics:
    - rootless=False: needs IPC_LOCK (mlock shared_buffers)
    - memory-swap = memory (no swap for database)
    - shm_size = container_ram × 25% (PostgreSQL shared_buffers)
    - oom_score_adj = -500 (protected from OOM kill)
    - nofile = 1048576 (1 FD per DB connection)
    """
    return JSONResponse({
        "mode":               "new",
        "host_cpu_cores":     8,
        "host_ram_gb":        32,
        "os_type":            "rhel-9",
        "container_cpu_cores":4.0,
        "container_ram_gb":   8.0,
        "container_type":     "database",
        "rootless":           False,
        "cgroup_version":     "v2",
        "use_quadlet":        True,
        "network_mode":       "host",
        "expected_pids":      1024,
        "shm_size_mb":        512,
        "read_only_rootfs":   False,
        "drop_all_caps":      True,
    })


@router.post(
    "/example/existing",
    summary="Podman – Example EXISTING mode audit (common misconfigs)",
    include_in_schema=True,
)
def podman_example_existing() -> JSONResponse:
    """
    Common Podman misconfigs:
    - memory NOT SET (container can OOM host)
    - cpus NOT SET (container can consume all CPUs)
    - pids_limit=-1 (fork bomb possible)
    - ulimit nofile=1024:1024 (default — fails at 513th connection)
    - no security-opt no-new-privileges
    - no cap-drop
    - cgroup v1 (race conditions)
    - restart_policy=no (container stays down after crash)
    - rootless=False (unnecessarily rootful)
    """
    return JSONResponse({
        "mode":               "existing",
        "host_cpu_cores":     8,
        "host_ram_gb":        32,
        "os_type":            "rhel-9",
        "container_cpu_cores":2.0,
        "container_ram_gb":   4.0,
        "container_type":     "web",
        "rootless":           False,
        "cgroup_version":     "v1",
        "use_quadlet":        False,
        "network_mode":       "bridge",
        "expected_pids":      512,
        "shm_size_mb":        64,
        "read_only_rootfs":   False,
        "drop_all_caps":      False,
        "existing": {
            "cpu_shares":            1024,
            "cpus":                  None,
            "memory_mb":             None,
            "memory_swap_mb":        -1,
            "memory_reservation_mb": None,
            "pids_limit":            -1,
            "ulimit_nofile":         "1024:1024",
            "restart_policy":        "no",
            "rootless":              False,
            "security_opt":          [],
            "cgroup_v2":             False,
            "shm_size_mb":           64,
            "oom_score_adj":         0,
        },
    })
