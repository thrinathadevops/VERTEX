"""
app/api/v1/postgresql.py
========================
FastAPI router for the PostgreSQL tuning calculator.

Endpoints
---------
POST /api/v1/postgresql/calculate
POST /api/v1/postgresql/example/new
POST /api/v1/postgresql/example/existing
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.postgresql import PostgreSQLInput, PostgreSQLOutput
from app.calculators.postgresql_calculator import PostgreSQLCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=PostgreSQLOutput,
    summary="PostgreSQL – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- Memory allocation: shared_buffers, effective_cache_size, work_mem, maintenance_work_mem
- WAL tuning: wal_buffers, max_wal_size, checkpoint_completion_target
- Storage-aware planner: random_page_cost, effective_io_concurrency
- Parallel query: max_parallel_workers_per_gather tuned to workload type
- Complete postgresql.conf snippet
- OS sysctl block

**EXISTING mode** — audit current postgresql.conf:
- Identify misconfigured memory settings, wrong planner costs, disabled features
- Safe upgrade path with restart-required flags
    """,
)
def calculate_postgresql(inp: PostgreSQLInput) -> PostgreSQLOutput:
    try:
        result = PostgreSQLCalculator(inp).generate()
        logger.info(
            "PostgreSQL calculate",
            extra={
                "mode":             inp.mode.value,
                "ram_gb":           inp.ram_gb,
                "cpu_cores":        inp.cpu_cores,
                "shared_buffers":   result.shared_buffers,
                "work_mem":         result.work_mem,
                "max_connections":  inp.max_connections,
                "workload_type":    inp.workload_type,
            },
        )
        return result
    except ValueError as e:
        logger.warning("PostgreSQL validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="PostgreSQL – Example NEW mode request",
    include_in_schema=True,
)
def postgresql_example_new() -> JSONResponse:
    return JSONResponse({
        "mode":             "new",
        "cpu_cores":        8,
        "ram_gb":           32,
        "os_type":          "ubuntu-22",
        "storage_type":     "ssd",
        "max_connections":  200,
        "workload_type":    "oltp",
        "replication":      True,
    })


@router.post(
    "/example/existing",
    summary="PostgreSQL – Example EXISTING mode audit",
    include_in_schema=True,
)
def postgresql_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode":             "existing",
        "cpu_cores":        8,
        "ram_gb":           32,
        "os_type":          "rhel-9",
        "storage_type":     "ssd",
        "max_connections":  200,
        "workload_type":    "mixed",
        "replication":      True,
        "existing": {
            "shared_buffers":        "128MB",
            "effective_cache_size":  "4GB",
            "work_mem":              "4MB",
            "maintenance_work_mem":  "64MB",
            "max_connections":       100,
            "wal_buffers":           "-1",
            "checkpoint_completion_target": 0.5,
            "random_page_cost":      4.0,
            "effective_io_concurrency": 1,
            "max_worker_processes":  8,
            "max_parallel_workers":  2,
            "default_statistics_target": 100,
            "ssl_enabled":           False,
            "pg_version":            "16.2",
            "os_sysctl": {
                "vm.overcommit_memory": "0",
                "vm.swappiness":        "60",
                "net.core.somaxconn":   "128",
            },
        },
    })
