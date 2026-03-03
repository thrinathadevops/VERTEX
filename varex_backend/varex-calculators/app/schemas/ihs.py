"""
app/schemas/ihs.py
==================
Pydantic schemas for the IBM HTTP Server (IHS) tuning calculator.

IHS is Apache HTTPD 2.4-based but ships with IBM-specific defaults,
WebSphere Application Server (WAS) proxy module (mod_was_ap22_http /
mod_ibm_local_redirector), IBM GSKit for SSL (not OpenSSL),
and IBM WebSphere plugin-cfg.xml integration.

Three models:
  IHSExisting  — current httpd.conf / plugin-cfg.xml values for EXISTING mode audit
  IHSInput     — request body (NEW and EXISTING modes)
  IHSOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class IHSExisting(BaseModel):
    """
    Supply your current httpd.conf + plugin-cfg.xml values.
    All fields optional — only supplied fields are audited.
    """
    max_request_workers:         int   | None = None
    server_limit:                int   | None = None
    threads_per_child:           int   | None = None
    min_spare_threads:           int   | None = None
    max_spare_threads:           int   | None = None
    keep_alive:                  str   | None = None   # "On" / "Off"
    keep_alive_timeout:          int   | None = None   # seconds
    timeout:                     int   | None = None   # seconds
    server_tokens:               str   | None = None
    mpm_model:                   str   | None = None   # "event" / "worker"
    # plugin-cfg.xml values
    plugin_connect_timeout:      int   | None = None   # ConnectTimeout (seconds)
    plugin_io_timeout:           int   | None = None   # IOTimeout (seconds)
    plugin_retry_interval:       int   | None = None   # RetryInterval (seconds)
    plugin_max_connections:      int   | None = None   # MaxConnections per WAS node
    plugin_load_balance:         str   | None = None   # "Round Robin" / "Random"
    ssl_protocol:                str   | None = None   # GSKit SSL protocols
    ihs_version:                 str   | None = None   # e.g. "9.0.5.18"
    limit_request_line:          int   | None = None
    limit_request_field_size:    int   | None = None
    os_sysctl:                   dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class IHSInput(BaseModel):
    """
    Hardware + workload parameters for IBM HTTP Server tuning.

    mode
        new      → generate fresh IHS config from hardware + workload specs
        existing → audit IHSExisting values and return safe upgrade plan

    cpu_cores             : vCPU count
    ram_gb                : total RAM on host (GB)
    os_type               : host OS (IHS typically runs on AIX, RHEL, or Windows)
    expected_concurrent   : peak simultaneous HTTP connections
    avg_request_ms        : average request processing time (ms)
    mpm                   : event (IHS 9.0+) or worker
                            Note: prefork NOT recommended for IHS in production
    backend_type          : what IHS proxies to
                            was       → WebSphere Application Server via plugin-cfg.xml
                            liberty   → WebSphere Liberty via plugin-cfg.xml
                            custom    → generic reverse proxy via mod_proxy
                            none      → IHS standalone (static only)
    ssl_enabled           : TLS termination at IHS (uses IBM GSKit, not OpenSSL)
    was_cluster_size      : number of WAS / Liberty cluster members
    was_cell_name         : WAS cell name (used in plugin-cfg.xml path generation)
    dmgr_host             : Deployment Manager hostname for plugin propagation
    """
    mode:                 CalcMode = CalcMode.NEW

    cpu_cores:            Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:               Annotated[float, Field(gt=0,   le=4096)]
    os_type:              OSType   = OSType.RHEL_9
    expected_concurrent:  Annotated[int,   Field(ge=1)]
    avg_request_ms:       Annotated[int,   Field(ge=1,   le=300_000)]
    mpm:                  Literal["event", "worker"] = "event"
    backend_type:         Literal["was", "liberty", "custom", "none"] = "was"
    ssl_enabled:          bool = True
    was_cluster_size:     Annotated[int,   Field(ge=1,   le=256,  default=2)]
    was_cell_name:        str  = "myCell"
    dmgr_host:            str  = "dmgr.example.com"
    existing:             IHSExisting = Field(default_factory=IHSExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_was_proxy": {
                    "mode":               "new",
                    "cpu_cores":          8,
                    "ram_gb":             32,
                    "os_type":            "rhel-9",
                    "expected_concurrent":1000,
                    "avg_request_ms":     300,
                    "mpm":                "event",
                    "backend_type":       "was",
                    "ssl_enabled":        True,
                    "was_cluster_size":   3,
                    "was_cell_name":      "prodCell",
                    "dmgr_host":          "dmgr.example.com",
                },
                "new_liberty_proxy": {
                    "mode":               "new",
                    "cpu_cores":          8,
                    "ram_gb":             32,
                    "os_type":            "rhel-9",
                    "expected_concurrent":1500,
                    "avg_request_ms":     200,
                    "mpm":                "event",
                    "backend_type":       "liberty",
                    "ssl_enabled":        True,
                    "was_cluster_size":   4,
                    "was_cell_name":      "libertyCell",
                    "dmgr_host":          "dmgr.example.com",
                },
                "existing_audit": {
                    "mode":               "existing",
                    "cpu_cores":          4,
                    "ram_gb":             16,
                    "os_type":            "rhel-8",
                    "expected_concurrent":500,
                    "avg_request_ms":     300,
                    "mpm":                "worker",
                    "backend_type":       "was",
                    "ssl_enabled":        True,
                    "was_cluster_size":   2,
                    "was_cell_name":      "myCell",
                    "dmgr_host":          "dmgr.example.com",
                    "existing": {
                        "max_request_workers":      150,
                        "server_limit":             6,
                        "threads_per_child":        25,
                        "keep_alive":               "Off",
                        "keep_alive_timeout":       300,
                        "timeout":                  300,
                        "server_tokens":            "Full",
                        "mpm_model":                "worker",
                        "plugin_connect_timeout":   5,
                        "plugin_io_timeout":        60,
                        "plugin_retry_interval":    60,
                        "plugin_max_connections":   20,
                        "plugin_load_balance":      "Round Robin",
                        "ihs_version":              "9.0.5.18",
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
class IHSOutput(BaseModel):
    """Full IHS calculator response."""
    mode:                        CalcMode

    # ── calculated values ──
    max_request_workers:         int
    server_limit:                int
    threads_per_child:           int
    min_spare_threads:           int
    max_spare_threads:           int
    estimated_max_clients:       int

    # ── plugin-cfg.xml values ──
    plugin_connect_timeout:      int    # seconds
    plugin_io_timeout:           int    # seconds
    plugin_max_connections:      int    # per WAS/Liberty member

    # ── ready-to-use config ──
    ihs_conf_snippet:            str
    plugin_cfg_snippet:          str    # plugin-cfg.xml ServerCluster block

    # ── tiered params ──
    major_params:                list[TuningParam]
    medium_params:               list[TuningParam]
    minor_params:                list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:              str

    # ── advisory outputs ──
    ha_suggestions:              list[str]
    performance_warnings:        list[str]
    capacity_warning:            str | None

    # ── EXISTING mode only ──
    audit_findings:              list[str] = []
