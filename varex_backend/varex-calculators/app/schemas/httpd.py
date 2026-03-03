"""
app/schemas/httpd.py
====================
Pydantic schemas for the Apache HTTPD tuning calculator.

Three models:
  HttpdExisting  — current httpd.conf values for EXISTING mode audit
  HttpdInput     — request body (NEW and EXISTING modes)
  HttpdOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class HttpdExisting(BaseModel):
    """
    Supply your current httpd.conf / mpm.conf values.
    All fields optional — only supplied fields are audited.

    os_sysctl: current kernel values for OS-level audit, e.g.
               {"net.core.somaxconn": "128", "vm.swappiness": "60"}
    """
    max_request_workers:      int   | None = None  # MaxRequestWorkers / MaxClients
    server_limit:             int   | None = None  # ServerLimit
    threads_per_child:        int   | None = None  # ThreadsPerChild (event/worker)
    min_spare_threads:        int   | None = None  # MinSpareThreads
    max_spare_threads:        int   | None = None  # MaxSpareThreads
    start_servers:            int   | None = None  # StartServers
    max_connections_per_child:int   | None = None  # MaxConnectionsPerChild
    keep_alive:               str   | None = None  # "On" or "Off"
    keep_alive_timeout:       int   | None = None  # KeepAliveTimeout (seconds)
    max_keep_alive_requests:  int   | None = None  # MaxKeepAliveRequests
    timeout:                  int   | None = None  # Timeout (seconds)
    limit_request_line:       int   | None = None  # LimitRequestLine (bytes)
    limit_request_field_size: int   | None = None  # LimitRequestFieldSize (bytes)
    limit_request_body:       int   | None = None  # LimitRequestBody (bytes)
    send_buffer_size:         int   | None = None  # SendBufferSize (bytes)
    receive_buffer_size:      int   | None = None  # ReceiveBufferSize (bytes)
    server_tokens:            str   | None = None  # "Full", "OS", "Minimal", "Minor", "Major", "Prod"
    mpm_model:                str   | None = None  # "event", "worker", "prefork"
    apache_version:           str   | None = None  # e.g. "2.4.58"
    os_sysctl:                dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class HttpdInput(BaseModel):
    """
    Hardware + workload parameters for Apache HTTPD tuning.

    mode
        new      → generate fresh httpd.conf from hardware + workload specs
        existing → audit HttpdExisting values and return safe upgrade plan

    cpu_cores           : vCPU count
    ram_gb              : total RAM on host (GB)
    os_type             : host OS — drives OS sysctl recommendations
    expected_concurrent : peak simultaneous HTTP connections
    avg_request_ms      : average request processing time (ms)
    mpm                 : Multi-Processing Module
                          event   → default 2.4+, event-driven, handles keep-alive
                                    via dedicated listener thread (best for most workloads)
                          worker  → thread-based, lower RAM than prefork, no keep-alive listener
                          prefork → 1 process per connection, non-threaded
                                    (required for non-thread-safe modules e.g. mod_php)
    ssl_enabled         : TLS termination at HTTPD
    reverse_proxy       : HTTPD acting as proxy to backend (adds proxy_* params)
    serve_static        : serving static files (adds mod_cache / file cache hints)
    """
    mode:               CalcMode = CalcMode.NEW

    cpu_cores:          Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:             Annotated[float, Field(gt=0,   le=4096)]
    os_type:            OSType   = OSType.UBUNTU_22
    expected_concurrent:Annotated[int,   Field(ge=1)]
    avg_request_ms:     Annotated[int,   Field(ge=1,   le=300_000)]
    mpm:                Literal["event", "worker", "prefork"] = "event"
    ssl_enabled:        bool = True
    reverse_proxy:      bool = False
    serve_static:       bool = True
    existing:           HttpdExisting = Field(default_factory=HttpdExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_event_mpm": {
                    "mode":               "new",
                    "cpu_cores":          8,
                    "ram_gb":             32,
                    "os_type":            "ubuntu-22",
                    "expected_concurrent":2000,
                    "avg_request_ms":     150,
                    "mpm":                "event",
                    "ssl_enabled":        True,
                    "reverse_proxy":      True,
                    "serve_static":       True,
                },
                "existing_audit_prefork": {
                    "mode":               "existing",
                    "cpu_cores":          4,
                    "ram_gb":             16,
                    "os_type":            "rhel-8",
                    "expected_concurrent":500,
                    "avg_request_ms":     200,
                    "mpm":                "prefork",
                    "ssl_enabled":        True,
                    "reverse_proxy":      False,
                    "serve_static":       True,
                    "existing": {
                        "max_request_workers":      150,
                        "server_limit":             150,
                        "threads_per_child":        25,
                        "keep_alive":               "Off",
                        "keep_alive_timeout":       300,
                        "timeout":                  300,
                        "server_tokens":            "Full",
                        "mpm_model":                "prefork",
                        "apache_version":           "2.4.51",
                        "os_sysctl": {
                            "net.core.somaxconn":  "128",
                            "vm.swappiness":       "60",
                        },
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class HttpdOutput(BaseModel):
    """Full Apache HTTPD calculator response."""
    mode:                    CalcMode

    # ── calculated values ──
    max_request_workers:     int
    server_limit:            int
    threads_per_child:       int
    min_spare_threads:       int
    max_spare_threads:       int
    estimated_max_clients:   int

    # ── ready-to-use config ──
    httpd_conf_snippet:      str

    # ── tiered params ──
    major_params:            list[TuningParam]
    medium_params:           list[TuningParam]
    minor_params:            list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:          str

    # ── advisory outputs ──
    ha_suggestions:          list[str]
    performance_warnings:    list[str]
    capacity_warning:        str | None

    # ── EXISTING mode only ──
    audit_findings:          list[str] = []
