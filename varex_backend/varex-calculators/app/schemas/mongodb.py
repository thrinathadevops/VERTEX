"""
app/schemas/mongodb.py
======================
Pydantic schemas for the MongoDB tuning calculator.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class MongoDBExisting(BaseModel):
    """Current mongod.conf values for EXISTING mode audit."""
    wired_tiger_cache_size_gb: float | None = None
    max_connections:           int   | None = None
    oplog_size_mb:             int   | None = None
    journal_enabled:           bool         = True
    journal_commit_interval:   int   | None = None   # ms
    storage_engine:            str   | None = None   # "wiredTiger"
    auth_enabled:              bool         = False
    ssl_mode:                  str   | None = None   # "disabled","requireSSL"
    mongodb_version:           str   | None = None   # e.g. "7.0.6"
    os_sysctl:                 dict[str, str] = {}


class MongoDBInput(BaseModel):
    """Hardware + workload parameters for MongoDB tuning."""
    mode:              CalcMode = CalcMode.NEW

    cpu_cores:         Annotated[int,   Field(ge=1,    le=512)]
    ram_gb:            Annotated[float, Field(gt=0,    le=4096)]
    os_type:           OSType    = OSType.UBUNTU_22
    storage_type:      Literal["hdd", "ssd", "nvme"] = "ssd"
    disk_size_gb:      Annotated[float, Field(gt=0,    default=500)]
    max_connections:   Annotated[int,   Field(ge=1,    le=65536,  default=5000)]
    workload_type:     Literal["operational", "analytics", "mixed"] = "operational"
    replica_set:       bool  = True
    sharded:           bool  = False
    existing:          MongoDBExisting = Field(default_factory=MongoDBExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new": {
                    "mode": "new",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "ubuntu-22",
                    "storage_type": "ssd",
                    "disk_size_gb": 500,
                    "max_connections": 5000,
                    "workload_type": "operational",
                    "replica_set": True,
                    "sharded": False,
                },
                "existing": {
                    "mode": "existing",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "rhel-9",
                    "storage_type": "ssd",
                    "disk_size_gb": 500,
                    "max_connections": 5000,
                    "workload_type": "mixed",
                    "replica_set": True,
                    "sharded": False,
                    "existing": {
                        "wired_tiger_cache_size_gb": 10,
                        "max_connections": 5000,
                        "oplog_size_mb": 1024,
                        "journal_enabled": True,
                        "auth_enabled": False,
                        "ssl_mode": "disabled",
                        "mongodb_version": "7.0.6",
                        "os_sysctl": {
                            "vm.swappiness": "60",
                            "transparent_hugepage": "always",
                        },
                    },
                },
            }
        }
    }


class MongoDBOutput(BaseModel):
    """Full MongoDB calculator response."""
    mode:                        CalcMode

    wired_tiger_cache_gb:        float
    recommended_oplog_mb:        int
    recommended_max_connections: int

    mongod_conf_snippet:         str

    major_params:                list[TuningParam]
    medium_params:               list[TuningParam]
    minor_params:                list[TuningParam]

    os_sysctl_conf:              str

    ha_suggestions:              list[str]
    performance_warnings:        list[str]
    capacity_warning:            str | None

    audit_findings:              list[str] = []
