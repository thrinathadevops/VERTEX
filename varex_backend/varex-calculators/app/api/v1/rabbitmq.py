"""
app/api/v1/rabbitmq.py
======================
FastAPI router for the RabbitMQ tuning calculator.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.rabbitmq import RabbitMQInput, RabbitMQOutput
from app.calculators.rabbitmq_calculator import RabbitMQCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=RabbitMQOutput,
    summary="RabbitMQ – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — memory watermark, disk limits, channels, Erlang VM, clustering.
**EXISTING mode** — audit current rabbitmq.conf and identify misconfigurations.
    """,
)
def calculate_rabbitmq(inp: RabbitMQInput) -> RabbitMQOutput:
    try:
        result = RabbitMQCalculator(inp).generate()
        logger.info(
            "RabbitMQ calculate",
            extra={"mode": inp.mode.value, "ram_gb": inp.ram_gb,
                   "watermark": result.vm_memory_high_watermark},
        )
        return result
    except ValueError as e:
        logger.warning("RabbitMQ validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/example/new", summary="RabbitMQ – Example NEW mode request")
def rabbitmq_example_new() -> JSONResponse:
    return JSONResponse({
        "mode": "new", "cpu_cores": 4, "ram_gb": 8, "os_type": "ubuntu-22",
        "expected_publishers": 50, "expected_consumers": 50,
        "expected_queues": 100, "message_size_kb": 4, "messages_per_sec": 5000,
        "clustered": True, "cluster_nodes": 3,
    })


@router.post("/example/existing", summary="RabbitMQ – Example EXISTING mode audit")
def rabbitmq_example_existing() -> JSONResponse:
    return JSONResponse({
        "mode": "existing", "cpu_cores": 4, "ram_gb": 8, "os_type": "rhel-9",
        "expected_publishers": 100, "expected_consumers": 100,
        "expected_queues": 200, "message_size_kb": 4, "messages_per_sec": 10000,
        "clustered": True, "cluster_nodes": 3,
        "existing": {
            "vm_memory_high_watermark": 0.4, "disk_free_limit": "50MB",
            "channel_max": 128, "heartbeat": 60, "max_connections": 256,
            "management_enabled": True, "ssl_enabled": False,
            "rabbitmq_version": "3.13.1",
            "os_sysctl": {"fs.file-max": "65536", "net.core.somaxconn": "128"},
        },
    })
