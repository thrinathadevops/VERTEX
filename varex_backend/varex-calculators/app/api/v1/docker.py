"""
app/api/v1/docker.py
====================
FastAPI router for the Docker daemon tuning calculator.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.docker import DockerInput, DockerOutput
from app.calculators.docker_calculator import DockerCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=DockerOutput,
    summary="Docker – Calculate optimal daemon config (NEW & EXISTING modes)",
    description="""
**NEW mode** — daemon.json: storage driver, log rotation, ulimits, security.
**EXISTING mode** — audit current daemon.json and identify misconfigurations.
    """,
)
def calculate_docker(inp: DockerInput) -> DockerOutput:
    try:
        result = DockerCalculator(inp).generate()
        logger.info(
            "Docker calculate",
            extra={"mode": inp.mode.value, "ram_gb": inp.ram_gb,
                   "containers": inp.container_count},
        )
        return result
    except ValueError as e:
        logger.warning("Docker validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/example/new", summary="Docker – Example NEW mode request")
def docker_example_new() -> JSONResponse:
    return JSONResponse({
        "mode": "new", "cpu_cores": 8, "ram_gb": 32, "os_type": "ubuntu-22",
        "container_count": 20, "container_type": "mixed",
    })


@router.post("/example/existing", summary="Docker – Example EXISTING mode audit")
def docker_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode": "existing", "cpu_cores": 8, "ram_gb": 32, "os_type": "rhel-9",
        "container_count": 50, "container_type": "web",
        "existing": {
            "storage_driver": "overlay2", "log_driver": "json-file",
            "log_max_size": "100m", "log_max_file": 10, "live_restore": False,
            "userland_proxy": True, "default_ulimits_nofile": 1024,
            "max_concurrent_downloads": 3, "docker_version": "25.0.3",
            "os_sysctl": {"net.core.somaxconn": "128", "vm.swappiness": "60"},
        },
    })
