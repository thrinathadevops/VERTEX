from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class RedisExistingConfig(BaseModel):
    maxmemory_gb:       float | None = None
    maxmemory_policy:   str   | None = None
    appendonly:         str   | None = None   # "yes" / "no"
    hz:                 int   | None = None
    tcp_backlog:        int   | None = None
    redis_version:      str   | None = None
    os_sysctl:          dict[str, str] = Field(default_factory=dict)


class RedisInput(BaseModel):
    mode:            CalcMode = CalcMode.NEW
    cpu_cores:       Annotated[int,   Field(ge=1, le=512)]
    ram_gb:          Annotated[float, Field(gt=0, le=4096)]
    os_type:         OSType = OSType.UBUNTU_22
    avg_key_size_kb: Annotated[float, Field(gt=0, le=102_400)]
    estimated_keys:  Annotated[int,   Field(ge=1)]
    persistence:     Literal["none", "rdb", "aof", "rdb+aof"] = "rdb"
    replication:     bool = False
    cluster_nodes:   Annotated[int,   Field(ge=1, le=1000, default=1)]
    peak_ops_per_sec: Annotated[int,  Field(ge=1, default=10_000)]
    existing:        RedisExistingConfig = Field(default_factory=RedisExistingConfig)

    model_config = {"json_schema_extra": {"examples": {
        "new": {"mode": "new", "cpu_cores": 4, "ram_gb": 32, "os_type": "ubuntu-22",
                "avg_key_size_kb": 2, "estimated_keys": 5_000_000,
                "persistence": "aof", "replication": True, "cluster_nodes": 3, "peak_ops_per_sec": 50_000},
        "existing": {"mode": "existing", "cpu_cores": 4, "ram_gb": 32, "os_type": "rhel-8",
                     "avg_key_size_kb": 2, "estimated_keys": 5_000_000,
                     "persistence": "aof", "replication": True, "cluster_nodes": 1, "peak_ops_per_sec": 50_000,
                     "existing": {"maxmemory_gb": 28, "maxmemory_policy": "noeviction",
                                  "appendonly": "no", "hz": 10,
                                  "os_sysctl": {"vm.overcommit_memory": "0",
                                                "transparent_hugepage": "always"}}}
    }}}


class RedisOutput(BaseModel):
    mode:                     CalcMode
    estimated_dataset_gb:     float
    recommended_maxmemory_gb: float
    maxmemory_reserved_gb:    float
    eviction_policy:          str
    redis_conf_snippet:       str
    major_params:             list[TuningParam]
    medium_params:            list[TuningParam]
    minor_params:             list[TuningParam]
    os_sysctl_conf:           str
    ha_suggestions:           list[str]
    performance_warnings:     list[str]
    capacity_warning:         str | None
    audit_findings:           list[str] = []
