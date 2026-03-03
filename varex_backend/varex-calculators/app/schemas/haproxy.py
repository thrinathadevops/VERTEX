"""
app/schemas/haproxy.py
======================
Pydantic schemas for the HAProxy tuning calculator.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class HAProxyExisting(BaseModel):
    """Current haproxy.cfg values for EXISTING mode audit."""
    global_maxconn:    int   | None = None
    frontend_maxconn:  int   | None = None
    nbthread:          int   | None = None
    timeout_connect:   str   | None = None   # e.g. "5s"
    timeout_client:    str   | None = None
    timeout_server:    str   | None = None
    ssl_enabled:       bool         = False
    stats_enabled:     bool         = False
    haproxy_version:   str   | None = None
    os_sysctl:         dict[str, str] = {}


class HAProxyInput(BaseModel):
    """Hardware + workload parameters for HAProxy tuning."""
    mode:                CalcMode = CalcMode.NEW

    cpu_cores:           Annotated[int,   Field(ge=1,    le=256)]
    ram_gb:              Annotated[float, Field(gt=0,    le=1024)]
    os_type:             OSType    = OSType.UBUNTU_22
    expected_concurrent: Annotated[int,   Field(ge=1,    default=10000)]
    backend_count:       Annotated[int,   Field(ge=1,    le=1000, default=4)]
    ssl_enabled:         bool  = True
    http_mode:           Literal["http", "tcp"] = "http"
    existing:            HAProxyExisting = Field(default_factory=HAProxyExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new": {
                    "mode": "new",
                    "cpu_cores": 4,
                    "ram_gb": 8,
                    "os_type": "ubuntu-22",
                    "expected_concurrent": 10000,
                    "backend_count": 4,
                    "ssl_enabled": True,
                    "http_mode": "http",
                },
                "existing": {
                    "mode": "existing",
                    "cpu_cores": 4,
                    "ram_gb": 8,
                    "os_type": "rhel-9",
                    "expected_concurrent": 10000,
                    "backend_count": 4,
                    "ssl_enabled": True,
                    "http_mode": "http",
                    "existing": {
                        "global_maxconn": 2000,
                        "frontend_maxconn": 1000,
                        "nbthread": 1,
                        "timeout_connect": "5s",
                        "timeout_client": "50s",
                        "timeout_server": "50s",
                        "ssl_enabled": False,
                        "stats_enabled": False,
                        "haproxy_version": "2.8.5",
                        "os_sysctl": {
                            "net.core.somaxconn": "128",
                            "net.ipv4.ip_local_port_range": "32768 60999",
                        },
                    },
                },
            }
        }
    }


class HAProxyOutput(BaseModel):
    """Full HAProxy calculator response."""
    mode:                      CalcMode

    global_maxconn:            int
    frontend_maxconn:          int
    nbthread:                  int

    haproxy_cfg_snippet:       str

    major_params:              list[TuningParam]
    medium_params:             list[TuningParam]
    minor_params:              list[TuningParam]

    os_sysctl_conf:            str

    ha_suggestions:            list[str]
    performance_warnings:      list[str]
    capacity_warning:          str | None

    audit_findings:            list[str] = []
