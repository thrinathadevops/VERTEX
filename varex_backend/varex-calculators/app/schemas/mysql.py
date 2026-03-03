"""
app/schemas/mysql.py
====================
Pydantic schemas for the MySQL/MariaDB tuning calculator.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class MySQLExisting(BaseModel):
    """Current my.cnf values for EXISTING mode audit."""
    innodb_buffer_pool_size:      str   | None = None   # e.g. "8G"
    innodb_buffer_pool_instances: int   | None = None
    innodb_log_file_size:         str   | None = None   # e.g. "256M"
    innodb_flush_log_at_trx_commit: int | None = None   # 0, 1, or 2
    innodb_io_capacity:           int   | None = None
    innodb_io_capacity_max:       int   | None = None
    max_connections:              int   | None = None
    thread_pool_size:             int   | None = None
    table_open_cache:             int   | None = None
    query_cache_type:             int   | None = None   # 0=off (8.0 removed it)
    tmp_table_size:               str   | None = None
    max_heap_table_size:          str   | None = None
    binlog_enabled:               bool         = True
    ssl_enabled:                  bool         = False
    mysql_version:                str   | None = None   # e.g. "8.0.36"
    os_sysctl:                    dict[str, str] = {}


class MySQLInput(BaseModel):
    """
    Hardware + workload parameters for MySQL tuning.

    storage_type : hdd, ssd, or nvme — drives innodb_io_capacity
    dedicated    : True if this is a dedicated MySQL server (80% RAM for InnoDB)
    """
    mode:            CalcMode = CalcMode.NEW

    cpu_cores:       Annotated[int,   Field(ge=1,    le=512)]
    ram_gb:          Annotated[float, Field(gt=0,    le=4096)]
    os_type:         OSType    = OSType.UBUNTU_22
    storage_type:    Literal["hdd", "ssd", "nvme"] = "ssd"
    max_connections: Annotated[int,   Field(ge=1,    le=50000, default=200)]
    workload_type:   Literal["oltp", "olap", "mixed"] = "oltp"
    dedicated:       bool  = True
    replication:     bool  = False
    existing:        MySQLExisting = Field(default_factory=MySQLExisting)

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
                    "dedicated": True,
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
                    "dedicated": True,
                    "replication": False,
                    "existing": {
                        "innodb_buffer_pool_size": "4G",
                        "innodb_buffer_pool_instances": 1,
                        "innodb_log_file_size": "48M",
                        "innodb_flush_log_at_trx_commit": 1,
                        "innodb_io_capacity": 200,
                        "max_connections": 151,
                        "thread_pool_size": 4,
                        "table_open_cache": 2000,
                        "query_cache_type": 1,
                        "binlog_enabled": False,
                        "ssl_enabled": False,
                        "mysql_version": "8.0.36",
                        "os_sysctl": {
                            "vm.swappiness": "60",
                            "net.core.somaxconn": "128",
                        },
                    },
                },
            }
        }
    }


class MySQLOutput(BaseModel):
    """Full MySQL calculator response."""
    mode:                          CalcMode

    innodb_buffer_pool_size:       str
    innodb_buffer_pool_instances:  int
    innodb_log_file_size:          str
    innodb_io_capacity:            int
    recommended_max_connections:   int

    my_cnf_snippet:                str

    major_params:                  list[TuningParam]
    medium_params:                 list[TuningParam]
    minor_params:                  list[TuningParam]

    os_sysctl_conf:                str

    ha_suggestions:                list[str]
    performance_warnings:          list[str]
    capacity_warning:              str | None

    audit_findings:                list[str] = []
