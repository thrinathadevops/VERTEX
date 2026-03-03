"""
app/schemas/nginx.py
====================
Pydantic schemas for the NGINX tuning calculator.

Three models:
  NginxExisting  — current config values supplied in EXISTING mode audit
  NginxInput     — request body (both NEW and EXISTING modes)
  NginxOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class NginxExisting(BaseModel):
    """
    Supply any values you currently have set.
    Fields left as None are skipped during audit.
    os_sysctl: pass current sysctl values for OS-level audit,
               e.g. {"net.core.somaxconn": "128", "vm.swappiness": "60"}
    """
    worker_processes:             int   | None = None
    worker_connections:           int   | None = None
    worker_rlimit_nofile:         int   | None = None
    keepalive_timeout:            int   | None = None
    client_max_body_size:         str   | None = None
    client_header_buffer_size:    str   | None = None
    large_client_header_buffers:  str   | None = None
    client_body_buffer_size:      str   | None = None
    client_body_timeout:          int   | None = None
    send_timeout:                 int   | None = None
    reset_timedout_connection:    str   | None = None
    ssl_protocols:                str   | None = None
    ssl_session_timeout:          str   | None = None
    ssl_buffer_size:              str   | None = None
    server_tokens:                str   | None = None
    gzip:                         str   | None = None
    nginx_version:                str   | None = None
    os_sysctl:                    dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class NginxInput(BaseModel):
    """
    Hardware + workload parameters used to calculate optimal NGINX config.

    mode
        new      → generate fresh config from hardware + workload specs
        existing → audit NginxExisting values and return safe upgrade plan

    cpu_cores          : vCPU count (= worker_processes)
    ram_gb             : total RAM available to NGINX (GB)
    os_type            : host OS — drives OS-specific sysctl recommendations
    expected_rps       : peak requests per second the server must handle
    avg_response_kb    : average response payload size in KB
                         (used to calculate per-connection memory cost)
    static_pct         : % of requests serving static files (0–100)
                         (affects open_file_cache sizing)
    keepalive_enabled  : whether HTTP keep-alive is in use
    ssl_enabled        : whether TLS termination happens at this NGINX
    reverse_proxy      : whether NGINX proxies to upstream backends
                         (adds proxy_* params and upstream keepalive)
    """
    mode:              CalcMode = CalcMode.NEW

    cpu_cores:         Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:            Annotated[float, Field(gt=0,   le=4096)]
    os_type:           OSType   = OSType.UBUNTU_22
    expected_rps:      Annotated[int,   Field(ge=1)]
    avg_response_kb:   Annotated[float, Field(gt=0,   le=102400)]
    static_pct:        Annotated[float, Field(ge=0,   le=100,   default=50)]
    keepalive_enabled: bool     = True
    ssl_enabled:       bool     = True
    reverse_proxy:     bool     = False
    existing:          NginxExisting = Field(default_factory=NginxExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_reverse_proxy": {
                    "mode": "new",
                    "cpu_cores": 8,
                    "ram_gb": 32,
                    "os_type": "ubuntu-22",
                    "expected_rps": 50000,
                    "avg_response_kb": 8,
                    "static_pct": 20,
                    "keepalive_enabled": True,
                    "ssl_enabled": True,
                    "reverse_proxy": True
                },
                "existing_audit": {
                    "mode": "existing",
                    "cpu_cores": 4,
                    "ram_gb": 16,
                    "os_type": "rhel-8",
                    "expected_rps": 10000,
                    "avg_response_kb": 4,
                    "static_pct": 50,
                    "keepalive_enabled": True,
                    "ssl_enabled": True,
                    "reverse_proxy": False,
                    "existing": {
                        "worker_processes": 2,
                        "worker_connections": 512,
                        "worker_rlimit_nofile": 1024,
                        "keepalive_timeout": 300,
                        "ssl_protocols": "TLSv1 TLSv1.1 TLSv1.2",
                        "ssl_buffer_size": "16k",
                        "server_tokens": "on",
                        "os_sysctl": {
                            "net.core.somaxconn": "128",
                            "vm.swappiness": "60"
                        }
                    }
                }
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class NginxOutput(BaseModel):
    """Full NGINX calculator response."""
    mode:                  CalcMode

    # ── calculated values ──
    worker_processes:      int
    worker_connections:    int
    worker_rlimit_nofile:  int
    keepalive_timeout:     int
    client_max_body_size:  str
    proxy_buffer_size:     str
    estimated_max_clients: int

    # ── ready-to-use config ──
    nginx_conf_snippet:    str

    # ── tiered params ──
    major_params:          list[TuningParam]
    medium_params:         list[TuningParam]
    minor_params:          list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:        str

    # ── advisory outputs ──
    ha_suggestions:        list[str]
    performance_warnings:  list[str]
    capacity_warning:      str | None

    # ── EXISTING mode only ──
    audit_findings:        list[str] = []
