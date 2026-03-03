"""
app/schemas/docker.py
=====================
Pydantic schemas for the Docker daemon tuning calculator.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class DockerExisting(BaseModel):
    """Current daemon.json values for EXISTING mode audit."""
    storage_driver:         str   | None = None   # "overlay2", "devicemapper"
    log_driver:             str   | None = None   # "json-file", "journald"
    log_max_size:           str   | None = None   # "50m"
    log_max_file:           int   | None = None
    live_restore:           bool         = False
    userland_proxy:         bool         = True
    default_ulimits_nofile: int   | None = None
    max_concurrent_downloads: int | None = None
    max_concurrent_uploads:   int | None = None
    docker_version:         str   | None = None
    os_sysctl:              dict[str, str] = {}


class DockerInput(BaseModel):
    """Hardware + workload parameters for Docker daemon tuning."""
    mode:              CalcMode = CalcMode.NEW

    cpu_cores:         Annotated[int,   Field(ge=1,    le=256)]
    ram_gb:            Annotated[float, Field(gt=0,    le=4096)]
    os_type:           OSType    = OSType.UBUNTU_22
    container_count:   Annotated[int,   Field(ge=1,    le=5000, default=20)]
    container_type:    Literal["web", "database", "worker", "mixed"] = "mixed"
    registry_mirror:   str | None = None
    existing:          DockerExisting = Field(default_factory=DockerExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new": {
                    "mode": "new",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "ubuntu-22",
                    "container_count": 20,
                    "container_type": "mixed",
                },
                "existing": {
                    "mode": "existing",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "rhel-9",
                    "container_count": 50,
                    "container_type": "web",
                    "existing": {
                        "storage_driver": "overlay2",
                        "log_driver": "json-file",
                        "log_max_size": "100m",
                        "log_max_file": 10,
                        "live_restore": False,
                        "userland_proxy": True,
                        "default_ulimits_nofile": 1024,
                        "max_concurrent_downloads": 3,
                        "docker_version": "25.0.3",
                        "os_sysctl": {
                            "net.core.somaxconn": "128",
                            "vm.swappiness": "60",
                        },
                    },
                },
            }
        }
    }


class DockerOutput(BaseModel):
    """Full Docker calculator response."""
    mode:                      CalcMode

    storage_driver:            str
    log_config:                str
    recommended_ulimits:       int

    daemon_json_snippet:       str

    major_params:              list[TuningParam]
    medium_params:             list[TuningParam]
    minor_params:              list[TuningParam]

    os_sysctl_conf:            str

    ha_suggestions:            list[str]
    performance_warnings:      list[str]
    capacity_warning:          str | None

    audit_findings:            list[str] = []
