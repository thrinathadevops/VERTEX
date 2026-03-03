"""
app/schemas/tomcat.py
=====================
Pydantic schemas for the Tomcat tuning calculator.

Three models:
  TomcatExisting  — current server.xml / JVM values for EXISTING mode audit
  TomcatInput     — request body (NEW and EXISTING modes)
  TomcatOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.varex_calculators.core.enums import OSType, CalcMode
from app.varex_calculators.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class TomcatExisting(BaseModel):
    """
    Supply your current server.xml + JVM startup values.
    All fields optional — only supplied fields are audited.
    """
    max_threads:               int   | None = None   # Connector maxThreads
    min_spare_threads:         int   | None = None   # Connector minSpareThreads
    accept_count:              int   | None = None   # Connector acceptCount
    connection_timeout:        int   | None = None   # Connector connectionTimeout (ms)
    max_connections:           int   | None = None   # Connector maxConnections
    keep_alive_timeout:        int   | None = None   # Connector keepAliveTimeout (ms)
    max_keep_alive_requests:   int   | None = None   # Connector maxKeepAliveRequests
    xms_gb:                    float | None = None   # -Xms in GB
    xmx_gb:                    float | None = None   # -Xmx in GB
    gc_type:                   str   | None = None   # e.g. "G1GC", "ParallelGC"
    metaspace_mb:              int   | None = None   # -XX:MaxMetaspaceSize in MB
    connector_protocol:        str   | None = None   # e.g. "HTTP/1.1", "org.apache.coyote.http11.Http11NioProtocol"
    compression:               str   | None = None   # "on"/"off"
    tomcat_version:            str   | None = None   # e.g. "10.1.18"
    os_sysctl:                 dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class TomcatInput(BaseModel):
    """
    Hardware + workload parameters for Tomcat tuning.

    mode
        new      → generate fresh server.xml + JVM flags from specs
        existing → audit TomcatExisting values and return safe upgrade plan

    cpu_cores          : vCPU count (direct multiplier for JVM GC threads)
    ram_gb             : total RAM on host (GB)
    os_type            : host OS — drives OS sysctl recommendations
    heap_ratio         : fraction of RAM to allocate as JVM heap (0.0–0.8)
                         default 0.50 — remaining 50% for OS, Metaspace, direct buffers
    target_concurrency : expected simultaneous HTTP requests
    avg_response_ms    : average request processing time in milliseconds
                         (used in Goetz formula for optimal thread count)
    io_wait_ratio      : fraction of request time spent waiting on I/O (0.0–1.0)
                         0.9 = 90% I/O-bound (DB queries, REST calls)
                         0.1 = 10% I/O-bound (CPU-heavy computation)
    connector_type     : NIO (default, event-driven) / NIO2 / APR
    ssl_enabled        : TLS termination at Tomcat (vs at NGINX/LB in front)
    compression_enabled: enable HTTP response compression via Tomcat
    gc_type            : JVM garbage collector
                         G1GC    → default Java 9+ (balanced throughput + pause time)
                         ZGC     → ultra-low pause (<1ms), Java 15+, high throughput
                         Shenandoah → low pause, Java 12+, Red Hat / OpenJDK
                         ParallelGC → max throughput, high pause (batch workloads only)
    java_version       : Java major version (affects GC defaults and flags)
    """
    mode:               CalcMode = CalcMode.NEW

    cpu_cores:          Annotated[int,   Field(ge=1,   le=512)]
    ram_gb:             Annotated[float, Field(gt=0,   le=4096)]
    os_type:            OSType   = OSType.UBUNTU_22
    heap_ratio:         Annotated[float, Field(gt=0.0, lt=0.9,  default=0.50)]
    target_concurrency: Annotated[int,   Field(ge=1)]
    avg_response_ms:    Annotated[int,   Field(ge=1,   le=300_000)]
    io_wait_ratio:      Annotated[float, Field(ge=0.0, le=1.0,  default=0.80)]
    connector_type:     Literal["NIO", "NIO2", "APR"] = "NIO"
    ssl_enabled:        bool = False   # usually False — SSL terminated at NGINX/LB
    compression_enabled:bool = True
    gc_type:            Literal["G1GC", "ZGC", "Shenandoah", "ParallelGC"] = "G1GC"
    java_version:       Annotated[int,   Field(ge=8,   le=24,   default=17)]
    existing:           TomcatExisting = Field(default_factory=TomcatExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_api_server": {
                    "mode":               "new",
                    "cpu_cores":          8,
                    "ram_gb":             32,
                    "os_type":            "ubuntu-22",
                    "heap_ratio":         0.50,
                    "target_concurrency": 500,
                    "avg_response_ms":    200,
                    "io_wait_ratio":      0.80,
                    "connector_type":     "NIO",
                    "ssl_enabled":        False,
                    "compression_enabled":True,
                    "gc_type":            "G1GC",
                    "java_version":       17,
                },
                "existing_audit": {
                    "mode":               "existing",
                    "cpu_cores":          4,
                    "ram_gb":             16,
                    "os_type":            "rhel-8",
                    "heap_ratio":         0.50,
                    "target_concurrency": 200,
                    "avg_response_ms":    300,
                    "io_wait_ratio":      0.80,
                    "connector_type":     "NIO",
                    "ssl_enabled":        False,
                    "compression_enabled":True,
                    "gc_type":            "G1GC",
                    "java_version":       11,
                    "existing": {
                        "max_threads":         150,
                        "min_spare_threads":   4,
                        "accept_count":        100,
                        "connection_timeout":  60000,
                        "xms_gb":              1.0,
                        "xmx_gb":              2.0,
                        "gc_type":             "ParallelGC",
                        "metaspace_mb":        128,
                        "connector_protocol":  "HTTP/1.1",
                        "compression":         "off",
                        "tomcat_version":      "9.0.83",
                        "os_sysctl": {
                            "net.core.somaxconn":    "128",
                            "vm.swappiness":         "60",
                            "transparent_hugepage":  "always",
                        },
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class TomcatOutput(BaseModel):
    """Full Tomcat calculator response."""
    mode:                   CalcMode

    # ── calculated values ──
    max_threads:            int      # Goetz formula result
    min_spare_threads:      int
    accept_count:           int
    xms_gb:                 float    # JVM heap -Xms
    xmx_gb:                 float    # JVM heap -Xmx
    metaspace_mb:           int
    gc_threads:             int

    # ── formula trace ──
    goetz_formula_trace:    str      # full Goetz N = U * C * (1 + W/C) working

    # ── ready-to-use config ──
    server_xml_snippet:     str
    jvm_flags:              str

    # ── tiered params ──
    major_params:           list[TuningParam]
    medium_params:          list[TuningParam]
    minor_params:           list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:         str

    # ── advisory outputs ──
    ha_suggestions:         list[str]
    performance_warnings:   list[str]
    capacity_warning:       str | None

    # ── EXISTING mode only ──
    audit_findings:         list[str] = []


