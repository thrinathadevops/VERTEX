"""
app/api/v1/mongodb.py
=====================
FastAPI router for the MongoDB tuning calculator.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.mongodb import MongoDBInput, MongoDBOutput
from app.calculators.mongodb_calculator import MongoDBCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=MongoDBOutput,
    summary="MongoDB – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — WiredTiger cache, oplog sizing, journal tuning, security hardening.
**EXISTING mode** — audit current mongod.conf and identify misconfigurations.
    """,
)
def calculate_mongodb(inp: MongoDBInput) -> MongoDBOutput:
    try:
        result = MongoDBCalculator(inp).generate()
        logger.info(
            "MongoDB calculate",
            extra={"mode": inp.mode.value, "ram_gb": inp.ram_gb,
                   "wt_cache": result.wired_tiger_cache_gb},
        )
        return result
    except ValueError as e:
        logger.warning("MongoDB validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/example/new", summary="MongoDB – Example NEW mode request")
def mongodb_example_new() -> JSONResponse:
    return JSONResponse({
        "mode": "new", "cpu_cores": 8, "ram_gb": 32, "os_type": "ubuntu-22",
        "storage_type": "ssd", "disk_size_gb": 500, "max_connections": 5000,
        "workload_type": "operational", "replica_set": True, "sharded": False,
    })


@router.post("/example/existing", summary="MongoDB – Example EXISTING mode audit")
def mongodb_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode": "existing", "cpu_cores": 8, "ram_gb": 32, "os_type": "rhel-9",
        "storage_type": "ssd", "disk_size_gb": 500, "max_connections": 5000,
        "workload_type": "mixed", "replica_set": True, "sharded": False,
        "existing": {
            "wired_tiger_cache_size_gb": 10, "max_connections": 5000,
            "oplog_size_mb": 1024, "journal_enabled": True,
            "auth_enabled": False, "ssl_mode": "disabled",
            "mongodb_version": "7.0.6",
            "os_sysctl": {"vm.swappiness": "60", "transparent_hugepage": "always"},
        },
    })
