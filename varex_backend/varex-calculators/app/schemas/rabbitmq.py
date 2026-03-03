"""
app/schemas/rabbitmq.py
=======================
Pydantic schemas for the RabbitMQ tuning calculator.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class RabbitMQExisting(BaseModel):
    """Current rabbitmq.conf values for EXISTING mode audit."""
    vm_memory_high_watermark:    float | None = None  # e.g. 0.4
    disk_free_limit:             str   | None = None  # e.g. "5GB"
    channel_max:                 int   | None = None
    heartbeat:                   int   | None = None  # seconds
    max_connections:             int   | None = None
    queue_master_locator:        str   | None = None
    cluster_partition_handling:  str   | None = None
    management_enabled:          bool         = False
    ssl_enabled:                 bool         = False
    rabbitmq_version:            str   | None = None  # e.g. "3.13.1"
    os_sysctl:                   dict[str, str] = {}


class RabbitMQInput(BaseModel):
    """Hardware + workload parameters for RabbitMQ tuning."""
    mode:                CalcMode = CalcMode.NEW

    cpu_cores:           Annotated[int,   Field(ge=1,    le=256)]
    ram_gb:              Annotated[float, Field(gt=0,    le=1024)]
    os_type:             OSType    = OSType.UBUNTU_22
    expected_publishers: Annotated[int,   Field(ge=1,    default=50)]
    expected_consumers:  Annotated[int,   Field(ge=1,    default=50)]
    expected_queues:     Annotated[int,   Field(ge=1,    default=100)]
    message_size_kb:     Annotated[float, Field(gt=0,    le=10240, default=4)]
    messages_per_sec:    Annotated[int,   Field(ge=1,    default=5000)]
    clustered:           bool  = True
    cluster_nodes:       Annotated[int,   Field(ge=1,    le=100,  default=3)]
    existing:            RabbitMQExisting = Field(default_factory=RabbitMQExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new": {
                    "mode": "new",
                    "cpu_cores": 4,
                    "ram_gb": 8,
                    "os_type": "ubuntu-22",
                    "expected_publishers": 50,
                    "expected_consumers": 50,
                    "expected_queues": 100,
                    "message_size_kb": 4,
                    "messages_per_sec": 5000,
                    "clustered": True,
                    "cluster_nodes": 3,
                },
                "existing": {
                    "mode": "existing",
                    "cpu_cores": 4,
                    "ram_gb": 8,
                    "os_type": "rhel-9",
                    "expected_publishers": 100,
                    "expected_consumers": 100,
                    "expected_queues": 200,
                    "message_size_kb": 4,
                    "messages_per_sec": 10000,
                    "clustered": True,
                    "cluster_nodes": 3,
                    "existing": {
                        "vm_memory_high_watermark": 0.4,
                        "disk_free_limit": "50MB",
                        "channel_max": 128,
                        "heartbeat": 60,
                        "max_connections": 256,
                        "management_enabled": True,
                        "ssl_enabled": False,
                        "rabbitmq_version": "3.13.1",
                        "os_sysctl": {
                            "fs.file-max": "65536",
                            "net.core.somaxconn": "128",
                        },
                    },
                },
            }
        }
    }


class RabbitMQOutput(BaseModel):
    """Full RabbitMQ calculator response."""
    mode:                         CalcMode

    vm_memory_high_watermark:     float
    recommended_disk_free_limit:  str
    recommended_channel_max:      int

    rabbitmq_conf_snippet:        str

    major_params:                 list[TuningParam]
    medium_params:                list[TuningParam]
    minor_params:                 list[TuningParam]

    os_sysctl_conf:               str

    ha_suggestions:               list[str]
    performance_warnings:         list[str]
    capacity_warning:             str | None

    audit_findings:               list[str] = []
