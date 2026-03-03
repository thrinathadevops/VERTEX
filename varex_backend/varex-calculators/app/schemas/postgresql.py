"""
app/schemas/postgresql.py
=========================
Pydantic schemas for the PostgreSQL tuning calculator.

Three models:
  PostgreSQLExisting — current postgresql.conf values for EXISTING mode audit
  PostgreSQLInput    — request body (NEW and EXISTING modes)
  PostgreSQLOutput   — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class PostgreSQLExisting(BaseModel):
    """
    Supply your current postgresql.conf values.
    All fields are optional — only supplied fields are audited.
    """
    shared_buffers:           str   | None = None   # e.g. "8GB"
    effective_cache_size:     str   | None = None   # e.g. "24GB"
    work_mem:                 str   | None = None   # e.g. "64MB"
    maintenance_work_mem:     str   | None = None   # e.g. "1GB"
    max_connections:          int   | None = None   # e.g. 200
    wal_buffers:              str   | None = None   # e.g. "64MB"
    max_wal_size:             str   | None = None   # e.g. "2GB"
    min_wal_size:             str   | None = None   # e.g. "1GB"
    checkpoint_completion_target: float | None = None  # e.g. 0.9
    random_page_cost:         float | None = None   # e.g. 1.1
    effective_io_concurrency: int   | None = None   # e.g. 200
    max_worker_processes:     int   | None = None
    max_parallel_workers:     int   | None = None
    max_parallel_workers_per_gather: int | None = None
    default_statistics_target: int  | None = None
    log_min_duration_statement: int | None = None   # ms
    ssl_enabled:              bool         = False
    pg_version:               str   | None = None   # e.g. "16.2"
    os_sysctl:                dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class PostgreSQLInput(BaseModel):
    """
    Hardware + workload parameters for PostgreSQL tuning.

    mode
        new      → generate fresh postgresql.conf from hardware + workload specs
        existing → audit current settings and return safe upgrade plan

    cpu_cores       : vCPU count
    ram_gb          : total RAM on the host (GB)
    os_type         : host OS — drives OS sysctl recommendations
    storage_type    : hdd, ssd, or nvme — affects random_page_cost & io_concurrency
    max_connections : expected max concurrent connections
    workload_type   : oltp (short queries, high concurrency), olap (long queries, analytics),
                      mixed (general purpose), data_warehouse (batch + reporting)
    replication     : True if streaming replication is used
    """
    mode:            CalcMode = CalcMode.NEW

    cpu_cores:       Annotated[int,   Field(ge=1,    le=512)]
    ram_gb:          Annotated[float, Field(gt=0,    le=4096)]
    os_type:         OSType    = OSType.UBUNTU_22
    storage_type:    Literal["hdd", "ssd", "nvme"] = "ssd"
    max_connections: Annotated[int,   Field(ge=1,    le=50000, default=200)]
    workload_type:   Literal["oltp", "olap", "mixed", "data_warehouse"] = "mixed"
    replication:     bool  = False
    existing:        PostgreSQLExisting = Field(default_factory=PostgreSQLExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new": {
                    "mode": "new",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "ubuntu-22",
                    "storage_type": "ssd",
                    "max_connections": 200,
                    "workload_type": "oltp",
                    "replication": True,
                },
                "existing": {
                    "mode": "existing",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "rhel-9",
                    "storage_type": "ssd",
                    "max_connections": 200,
                    "workload_type": "mixed",
                    "replication": True,
                    "existing": {
                        "shared_buffers": "128MB",
                        "effective_cache_size": "4GB",
                        "work_mem": "4MB",
                        "maintenance_work_mem": "64MB",
                        "max_connections": 100,
                        "wal_buffers": "-1",
                        "checkpoint_completion_target": 0.5,
                        "random_page_cost": 4.0,
                        "effective_io_concurrency": 1,
                        "max_worker_processes": 8,
                        "max_parallel_workers": 2,
                        "default_statistics_target": 100,
                        "ssl_enabled": False,
                        "pg_version": "16.2",
                        "os_sysctl": {
                            "vm.overcommit_memory": "0",
                            "vm.swappiness": "60",
                            "net.core.somaxconn": "128",
                        },
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class PostgreSQLOutput(BaseModel):
    """Full PostgreSQL calculator response."""
    mode:                      CalcMode

    # ── calculated values ──
    shared_buffers:            str      # e.g. "8GB"
    effective_cache_size:      str      # e.g. "24GB"
    work_mem:                  str      # e.g. "64MB"
    maintenance_work_mem:      str      # e.g. "1GB"
    recommended_max_connections: int
    wal_buffers:               str
    max_wal_size:              str

    # ── ready-to-use config ──
    postgresql_conf_snippet:   str

    # ── tiered params ──
    major_params:              list[TuningParam]
    medium_params:             list[TuningParam]
    minor_params:              list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:            str

    # ── advisory outputs ──
    ha_suggestions:            list[str]
    performance_warnings:      list[str]
    capacity_warning:          str | None

    # ── EXISTING mode only ──
    audit_findings:            list[str] = []
