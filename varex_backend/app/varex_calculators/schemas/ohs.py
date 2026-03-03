"""
app/schemas/ohs.py
==================
Pydantic schemas for the Oracle HTTP Server (OHS) tuning calculator.

OHS is Apache HTTPD 2.4-based but ships with Oracle-specific defaults,
WebLogic proxy module (mod_wl_ohs), Oracle SSO/SAML integrations,
and Oracle Fusion Middleware (FMW) deployment conventions.

Three models:
  OHSExisting  — current ohs.conf / httpd.conf values for EXISTING mode audit
  OHSInput     — request body (NEW and EXISTING modes)
  OHSOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.varex_calculators.core.enums import OSType, CalcMode
from app.varex_calculators.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class OHSExisting(BaseModel):
    """
    Supply your current OHS / httpd.conf values.
    All fields optional — only supplied fields are audited.
    """
    max_request_workers:      int   | None = None
    server_limit:             int   | None = None
    threads_per_child:        int   | None = None
    min_spare_threads:        int   | None = None
    max_spare_threads:        int   | None = None
    keep_alive:               str   | None = None   # "On" / "Off"
    keep_alive_timeout:       int   | None = None   # seconds
    timeout:                  int   | None = None   # seconds
    server_tokens:            str   | None = None
    mpm_model:                str   | None = None   # "event" / "worker"
    wl_connect_timeout:       int   | None = None   # WebLogic connect timeout ms
    wl_io_timeout:            int   | None = None   # WebLogic I/O timeout ms
    ssl_protocols:            str   | None = None
    ohs_version:              str   | None = None   # e.g. "12.2.1.4.0"
    limit_request_line:       int   | None = None
    limit_request_field_size: int   | None = None
    os_sysctl:                dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class OHSInput(BaseModel):
    """
    Hardware + workload parameters for Oracle HTTP Server tuning.

    mode
        new      → generate fresh OHS config from hardware + workload specs
        existing → audit OHSExisting values and return safe upgrade plan

    cpu_cores           : vCPU count
    ram_gb              : total RAM on host (GB)
    os_type             : host OS (OHS typically runs on Oracle Linux / RHEL)
    expected_concurrent : peak simultaneous HTTP connections
    avg_request_ms      : average request processing time (ms)
    mpm                 : event (recommended for OHS 12c+) or worker
                          Note: prefork NOT supported in OHS 12c (event/worker only)
    backend_type        : what OHS proxies to
                          weblogic  → mod_wl_ohs (WebLogic cluster)
                          fusion    → Oracle Fusion Apps (large SAML/SSO headers)
                          custom    → generic reverse proxy via mod_proxy
                          none      → OHS as standalone (static only)
    ssl_enabled         : TLS termination at OHS
    fusion_apps         : True if serving Oracle Fusion Middleware applications
                          (requires enlarged header buffers for SSO/SAML tokens)
    wls_cluster_size    : number of WebLogic Managed Server nodes in cluster
    """
    mode:               CalcMode = CalcMode.NEW

    cpu_cores:          Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:             Annotated[float, Field(gt=0,   le=4096)]
    os_type:            OSType   = OSType.RHEL_9
    expected_concurrent:Annotated[int,   Field(ge=1)]
    avg_request_ms:     Annotated[int,   Field(ge=1,   le=300_000)]
    mpm:                Literal["event", "worker"] = "event"
    backend_type:       Literal["weblogic", "fusion", "custom", "none"] = "weblogic"
    ssl_enabled:        bool = True
    fusion_apps:        bool = False
    wls_cluster_size:   Annotated[int,   Field(ge=1,   le=256,  default=2)]
    existing:           OHSExisting = Field(default_factory=OHSExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_weblogic_proxy": {
                    "mode":               "new",
                    "cpu_cores":          8,
                    "ram_gb":             32,
                    "os_type":            "rhel-9",
                    "expected_concurrent":1000,
                    "avg_request_ms":     250,
                    "mpm":                "event",
                    "backend_type":       "weblogic",
                    "ssl_enabled":        True,
                    "fusion_apps":        False,
                    "wls_cluster_size":   3,
                },
                "new_fusion_apps": {
                    "mode":               "new",
                    "cpu_cores":          16,
                    "ram_gb":             64,
                    "os_type":            "rhel-9",
                    "expected_concurrent":2000,
                    "avg_request_ms":     500,
                    "mpm":                "event",
                    "backend_type":       "fusion",
                    "ssl_enabled":        True,
                    "fusion_apps":        True,
                    "wls_cluster_size":   4,
                },
                "existing_audit": {
                    "mode":               "existing",
                    "cpu_cores":          4,
                    "ram_gb":             16,
                    "os_type":            "rhel-8",
                    "expected_concurrent":500,
                    "avg_request_ms":     300,
                    "mpm":                "worker",
                    "backend_type":       "weblogic",
                    "ssl_enabled":        True,
                    "fusion_apps":        False,
                    "wls_cluster_size":   2,
                    "existing": {
                        "max_request_workers":  150,
                        "server_limit":         6,
                        "threads_per_child":    25,
                        "keep_alive":           "Off",
                        "keep_alive_timeout":   300,
                        "timeout":              300,
                        "server_tokens":        "Full",
                        "mpm_model":            "worker",
                        "wl_connect_timeout":   10,
                        "wl_io_timeout":        300000,
                        "ohs_version":          "12.2.1.4.0",
                        "os_sysctl": {
                            "net.core.somaxconn": "128",
                            "vm.swappiness":      "60",
                        },
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class OHSOutput(BaseModel):
    """Full OHS calculator response."""
    mode:                    CalcMode

    # ── calculated values ──
    max_request_workers:     int
    server_limit:            int
    threads_per_child:       int
    min_spare_threads:       int
    max_spare_threads:       int
    estimated_max_clients:   int

    # ── ready-to-use config ──
    ohs_conf_snippet:        str

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


