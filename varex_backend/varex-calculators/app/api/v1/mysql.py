"""
app/api/v1/mysql.py
===================
FastAPI router for the MySQL tuning calculator.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.mysql import MySQLInput, MySQLOutput
from app.calculators.mysql_calculator import MySQLCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=MySQLOutput,
    summary="MySQL – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — InnoDB buffer pool, log files, I/O capacity, connections, replication.
**EXISTING mode** — audit current my.cnf and identify misconfigurations.
    """,
)
def calculate_mysql(inp: MySQLInput) -> MySQLOutput:
    try:
        result = MySQLCalculator(inp).generate()
        logger.info(
            "MySQL calculate",
            extra={"mode": inp.mode.value, "ram_gb": inp.ram_gb,
                   "buffer_pool": result.innodb_buffer_pool_size},
        )
        return result
    except ValueError as e:
        logger.warning("MySQL validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/example/new", summary="MySQL – Example NEW mode request")
def mysql_example_new() -> JSONResponse:
    return JSONResponse({
        "mode": "new", "cpu_cores": 8, "ram_gb": 32, "os_type": "ubuntu-22",
        "storage_type": "ssd", "max_connections": 200, "workload_type": "oltp",
        "dedicated": True, "replication": True,
    })


@router.post("/example/existing", summary="MySQL – Example EXISTING mode audit")
def mysql_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode": "existing", "cpu_cores": 8, "ram_gb": 32, "os_type": "rhel-9",
        "storage_type": "ssd", "max_connections": 200, "workload_type": "mixed",
        "dedicated": True, "replication": False,
        "existing": {
            "innodb_buffer_pool_size": "4G", "innodb_buffer_pool_instances": 1,
            "innodb_log_file_size": "48M", "innodb_flush_log_at_trx_commit": 1,
            "innodb_io_capacity": 200, "max_connections": 151,
            "query_cache_type": 1, "binlog_enabled": False, "ssl_enabled": False,
            "mysql_version": "8.0.36",
            "os_sysctl": {"vm.swappiness": "60", "net.core.somaxconn": "128"},
        },
    })
