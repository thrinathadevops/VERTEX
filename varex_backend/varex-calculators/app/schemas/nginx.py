from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, Field, model_validator
from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class NginxExistingConfig(BaseModel):
    """Fields populated only in EXISTING mode – all optional."""
    worker_processes:     int   | None = None
    worker_connections:   int   | None = None
    worker_rlimit_nofile: int   | None = None
    keepalive_timeout:    int   | None = None
    client_max_body_size: str   | None = None   # e.g. "10m"
    nginx_version:        str   | None = None   # e.g. "1.24.0"
    # raw sysctl values already on the OS
    os_sysctl: dict[str, str] = Field(
        default_factory=dict,
        description="Map of sysctl key→current value, e.g. {'net.core.somaxconn': '128'}"
    )


class NginxInput(BaseModel):
    mode:              CalcMode = CalcMode.NEW
    # ── Server hardware ──────────────────────────────────────────────────
    cpu_cores:         Annotated[int,   Field(ge=1,  le=512,    description="Physical/vCPU cores")]
    ram_gb:            Annotated[float, Field(gt=0,  le=4096,   description="Total usable RAM (GB)")]
    os_type:           OSType = OSType.UBUNTU_22
    # ── Workload ─────────────────────────────────────────────────────────
    expected_rps:      Annotated[int,   Field(ge=1,             description="Peak requests/sec")]
    avg_response_kb:   Annotated[float, Field(gt=0, le=102_400, description="Avg response size (KB)")]
    static_pct:        Annotated[float, Field(ge=0, le=100, default=50)]
    # ── Feature flags ────────────────────────────────────────────────────
    keepalive_enabled: bool = True
    ssl_enabled:       bool = True
    reverse_proxy:     bool = False
    # ── EXISTING mode payload ────────────────────────────────────────────
    existing: NginxExistingConfig = Field(default_factory=NginxExistingConfig)

    model_config = {"json_schema_extra": {"examples": {
        "new": {"mode": "new", "cpu_cores": 8, "ram_gb": 16, "os_type": "ubuntu-22",
                "expected_rps": 5000, "avg_response_kb": 32,
                "keepalive_enabled": True, "ssl_enabled": True, "reverse_proxy": True, "static_pct": 40},
        "existing": {"mode": "existing", "cpu_cores": 8, "ram_gb": 16, "os_type": "centos-7",
                     "expected_rps": 5000, "avg_response_kb": 32,
                     "keepalive_enabled": True, "ssl_enabled": True, "reverse_proxy": True,
                     "static_pct": 40,
                     "existing": {
                         "worker_processes": 2, "worker_connections": 512,
                         "worker_rlimit_nofile": 1024, "keepalive_timeout": 75,
                         "client_max_body_size": "1m",
                         "os_sysctl": {"net.core.somaxconn": "128", "vm.swappiness": "60"}}}
    }}}


class NginxOutput(BaseModel):
    mode:                   CalcMode
    worker_processes:       int
    worker_connections:     int
    worker_rlimit_nofile:   int
    keepalive_timeout:      int
    client_max_body_size:   str
    proxy_buffer_size:      str
    recommended_ulimit:     int
    estimated_max_clients:  int
    capacity_warning:       str | None
    nginx_conf_snippet:     str
    # Tiered param lists
    major_params:           list[TuningParam]
    medium_params:          list[TuningParam]
    minor_params:           list[TuningParam]
    os_sysctl_conf:         str
    ha_suggestions:         list[str]
    performance_warnings:   list[str]
    # EXISTING-only
    audit_findings:         list[str] = []
