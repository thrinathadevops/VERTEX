"""
app/schemas/iis.py
==================
Pydantic schemas for the Microsoft IIS (Internet Information Services)
tuning calculator.

IIS is Windows-native and fundamentally different from Apache-family servers:
  - Kernel-mode HTTP driver (http.sys) handles TCP accept + initial TLS
  - Application Pool worker processes (w3wp.exe) serve requests
  - Configuration via applicationHost.config (not httpd.conf)
  - Thread pool managed by CLR (.NET) or native IIS thread pool
  - Recycling: periodic w3wp.exe restart to clear memory leaks
  - IOCP (I/O Completion Ports): async I/O natively in Windows kernel

Three models:
  IISExisting  — current applicationHost.config values for EXISTING mode audit
  IISInput     — request body (NEW and EXISTING modes)
  IISOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class IISExisting(BaseModel):
    """
    Supply current applicationHost.config / App Pool values.
    All fields optional — only supplied fields are audited.
    """
    # App Pool
    max_processes:               int   | None = None  # maxProcesses (web garden)
    queue_length:                int   | None = None  # App Pool queue length
    rapid_fail_protection:       bool  | None = None  # rapidFailProtection
    recycle_minutes:             int   | None = None  # periodicRestart/time (minutes)
    recycle_requests:            int   | None = None  # periodicRestart/requests
    idle_timeout:                int   | None = None  # processModel/idleTimeout (minutes)
    max_worker_threads:          int   | None = None  # processModel/maxWorkerThreads
    max_io_threads:              int   | None = None  # processModel/maxIoThreads

    # Connection limits (site/server level)
    max_connections:             int   | None = None  # limits/maxConnections
    connection_timeout:          int   | None = None  # limits/connectionTimeout (seconds)
    header_wait_timeout:         int   | None = None  # headerWaitTimeout (seconds)
    min_bytes_per_second:        int   | None = None  # minBytesPerSecond

    # http.sys kernel queue
    kernel_queue_length:         int   | None = None  # http.sys request queue

    # TLS / cipher
    tls_protocols:               str   | None = None  # e.g. "TLS 1.0, TLS 1.1, TLS 1.2"
    iis_version:                 str   | None = None  # e.g. "10.0"

    # Output caching
    output_cache_enabled:        bool  | None = None

    # .NET / CLR
    dotnet_version:              str   | None = None  # e.g. "v4.0", "net8.0"
    managed_pipeline_mode:       str   | None = None  # "Integrated" / "Classic"


# ── request input ─────────────────────────────────────────────────────────
class IISInput(BaseModel):
    """
    Hardware + workload parameters for IIS tuning.

    mode
        new      → generate fresh applicationHost.config snippet + PowerShell
        existing → audit IISExisting values and return safe upgrade plan

    cpu_cores             : vCPU count (affects thread pool and web garden sizing)
    ram_gb                : total RAM on host (GB)
    os_type               : should be windows-server-2022 for IIS 10
    expected_concurrent   : peak simultaneous HTTP connections
    avg_request_ms        : average request processing time (ms)
    app_pool_count        : number of Application Pools
                            1  → single app, all resources to one pool
                            N  → multi-app, resources divided
    web_garden            : enable web garden (multiple w3wp.exe per App Pool)
                            True: scales CPU utilisation; False: simpler debugging
    dotnet_version        : .NET runtime version in the App Pool
                            net8.0 / net6.0 → ASP.NET Core (out-of-process hosting)
                            v4.0            → ASP.NET Framework 4.x (in-process)
                            none            → native / PHP / classic ASP
    managed_pipeline_mode : Integrated (default .NET 2.0+) or Classic (legacy)
    ssl_enabled           : TLS termination at IIS
    http2_enabled         : HTTP/2 support (IIS 10 / Windows Server 2016+)
    output_cache_enabled  : IIS kernel-mode output caching
    reverse_proxy         : IIS acting as ARR (Application Request Routing) proxy
    """
    mode:                 CalcMode = CalcMode.NEW

    cpu_cores:            Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:               Annotated[float, Field(gt=0,   le=4096)]
    os_type:              OSType   = OSType.WINDOWS_2022
    expected_concurrent:  Annotated[int,   Field(ge=1)]
    avg_request_ms:       Annotated[int,   Field(ge=1,   le=300_000)]
    app_pool_count:       Annotated[int,   Field(ge=1,   le=64,  default=1)]
    web_garden:           bool = False
    dotnet_version:       Literal["net8.0", "net6.0", "v4.0", "none"] = "net8.0"
    managed_pipeline_mode:Literal["Integrated", "Classic"] = "Integrated"
    ssl_enabled:          bool = True
    http2_enabled:        bool = True
    output_cache_enabled: bool = True
    reverse_proxy:        bool = False
    existing:             IISExisting = Field(default_factory=IISExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_aspnet_core": {
                    "mode":                 "new",
                    "cpu_cores":            8,
                    "ram_gb":               32,
                    "os_type":              "windows-server-2022",
                    "expected_concurrent":  1000,
                    "avg_request_ms":       150,
                    "app_pool_count":       1,
                    "web_garden":           False,
                    "dotnet_version":       "net8.0",
                    "managed_pipeline_mode":"Integrated",
                    "ssl_enabled":          True,
                    "http2_enabled":        True,
                    "output_cache_enabled": True,
                    "reverse_proxy":        False,
                },
                "new_aspnet_framework": {
                    "mode":                 "new",
                    "cpu_cores":            8,
                    "ram_gb":               32,
                    "os_type":              "windows-server-2022",
                    "expected_concurrent":  500,
                    "avg_request_ms":       300,
                    "app_pool_count":       2,
                    "web_garden":           True,
                    "dotnet_version":       "v4.0",
                    "managed_pipeline_mode":"Integrated",
                    "ssl_enabled":          True,
                    "http2_enabled":        True,
                    "output_cache_enabled": True,
                    "reverse_proxy":        False,
                },
                "existing_audit": {
                    "mode":                 "existing",
                    "cpu_cores":            4,
                    "ram_gb":               16,
                    "os_type":              "windows-server-2019",
                    "expected_concurrent":  500,
                    "avg_request_ms":       200,
                    "app_pool_count":       1,
                    "web_garden":           False,
                    "dotnet_version":       "v4.0",
                    "managed_pipeline_mode":"Classic",
                    "ssl_enabled":          True,
                    "http2_enabled":        False,
                    "output_cache_enabled": False,
                    "reverse_proxy":        False,
                    "existing": {
                        "max_processes":           1,
                        "queue_length":            1000,
                        "rapid_fail_protection":   True,
                        "recycle_minutes":         1740,
                        "recycle_requests":        0,
                        "idle_timeout":            20,
                        "max_worker_threads":      25,
                        "max_io_threads":          25,
                        "max_connections":         0,
                        "connection_timeout":      120,
                        "header_wait_timeout":     120,
                        "kernel_queue_length":     1000,
                        "tls_protocols":           "TLS 1.0, TLS 1.1, TLS 1.2",
                        "iis_version":             "10.0",
                        "output_cache_enabled":    False,
                        "dotnet_version":          "v4.0",
                        "managed_pipeline_mode":   "Classic",
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class IISOutput(BaseModel):
    """Full IIS calculator response."""
    mode:                        CalcMode

    # ── calculated values ──
    max_worker_threads:          int
    max_io_threads:              int
    queue_length:                int
    kernel_queue_length:         int
    recycle_minutes:             int
    max_processes:               int   # web garden processes
    private_memory_limit_kb:     int   # App Pool memory limit

    # ── ready-to-use config ──
    apphostconfig_snippet:       str   # applicationHost.config XML
    powershell_snippet:          str   # PowerShell WebAdministration commands

    # ── tiered params ──
    major_params:                list[TuningParam]
    medium_params:               list[TuningParam]
    minor_params:                list[TuningParam]

    # ── OS / registry tuning ──
    os_sysctl_conf:              str   # Windows registry + netsh commands

    # ── advisory outputs ──
    ha_suggestions:              list[str]
    performance_warnings:        list[str]
    capacity_warning:            str | None

    # ── EXISTING mode only ──
    audit_findings:              list[str] = []
