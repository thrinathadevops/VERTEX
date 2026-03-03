"""
app/schemas/podman.py
=====================
Pydantic schemas for the Podman container tuning calculator.

Podman is a daemonless OCI container runtime (libpod).
Key differences from Docker:
  - No central daemon — each container is a direct child of the calling process
  - Rootless mode: containers run as non-root user (user namespace remapping)
  - cgroup v2 native support (systemd integration via quadlets)
  - Compatible with Docker CLI but uses different resource limit mechanics
  - Pod concept (shared network namespace) — mirrors Kubernetes Pod semantics

Three models:
  PodmanExisting  — current container / pod run flags for EXISTING mode audit
  PodmanInput     — request body (NEW and EXISTING modes)
  PodmanOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class PodmanExisting(BaseModel):
    """
    Supply current podman run flags / quadlet unit values.
    All fields optional — only supplied fields are audited.
    """
    cpu_shares:              int   | None = None   # --cpu-shares (relative weight, default 1024)
    cpu_quota:               int   | None = None   # --cpu-quota (microseconds per period)
    cpu_period:              int   | None = None   # --cpu-period (default 100000 = 100ms)
    cpus:                    float | None = None   # --cpus (fractional CPU limit)
    memory_mb:               int   | None = None   # --memory in MB
    memory_swap_mb:          int   | None = None   # --memory-swap in MB (-1 = unlimited)
    memory_reservation_mb:   int   | None = None   # --memory-reservation (soft limit)
    pids_limit:              int   | None = None   # --pids-limit
    ulimit_nofile:           str   | None = None   # --ulimit nofile=<soft>:<hard>
    ulimit_nproc:            str   | None = None   # --ulimit nproc=<soft>:<hard>
    restart_policy:          str   | None = None   # --restart policy
    rootless:                bool  | None = None   # rootless mode
    security_opt:            list[str]    = []     # --security-opt entries
    sysctls:                 dict[str, str] = {}   # --sysctl entries
    cgroup_v2:               bool  | None = None
    shm_size_mb:             int   | None = None   # --shm-size in MB
    oom_score_adj:           int   | None = None   # --oom-score-adj


# ── request input ─────────────────────────────────────────────────────────
class PodmanInput(BaseModel):
    """
    Hardware + workload parameters for Podman container tuning.

    mode
        new      → generate podman run flags + quadlet systemd unit
        existing → audit PodmanExisting values and return safe upgrade plan

    host_cpu_cores        : total vCPU on the container host
    host_ram_gb           : total RAM on the container host (GB)
    os_type               : host OS
    container_cpu_cores   : CPU cores to allocate to this container
    container_ram_gb      : RAM to allocate to this container (GB)
    container_type        : workload type — drives specific limit recommendations
                            web       → HTTP server (NGINX/Tomcat in container)
                            worker    → background job / queue consumer
                            database  → Redis/Postgres/MySQL in container
                            cache     → pure in-memory cache
                            batch     → CPU-heavy short-lived batch job
    rootless              : run container as non-root (recommended)
    cgroup_version        : cgroup v1 (legacy) or v2 (recommended, systemd)
    use_quadlet           : generate systemd Quadlet .container unit (Podman 4.4+)
    network_mode          : bridge / host / slirp4netns (rootless default)
    expected_pids         : expected number of processes inside container
    shm_size_mb           : /dev/shm size (shared memory for IPC-heavy workloads)
    read_only_rootfs      : mount container root filesystem read-only (security)
    drop_all_caps         : drop ALL Linux capabilities, add back only required
    """
    mode:                 CalcMode = CalcMode.NEW

    host_cpu_cores:       Annotated[int,   Field(ge=1,   le=1024)]
    host_ram_gb:          Annotated[float, Field(gt=0,   le=4096)]
    os_type:              OSType   = OSType.RHEL_9
    container_cpu_cores:  Annotated[float, Field(gt=0,   le=512,  default=2.0)]
    container_ram_gb:     Annotated[float, Field(gt=0,   le=4096, default=4.0)]
    container_type:       Literal["web", "worker", "database", "cache", "batch"] = "web"
    rootless:             bool = True
    cgroup_version:       Literal["v1", "v2"] = "v2"
    use_quadlet:          bool = True
    network_mode:         Literal["bridge", "host", "slirp4netns", "pasta"] = "bridge"
    expected_pids:        Annotated[int,   Field(ge=1,   le=100_000, default=512)]
    shm_size_mb:          Annotated[int,   Field(ge=4,   le=65536,   default=64)]
    read_only_rootfs:     bool = True
    drop_all_caps:        bool = True
    existing:             PodmanExisting = Field(default_factory=PodmanExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_web_container": {
                    "mode":               "new",
                    "host_cpu_cores":     8,
                    "host_ram_gb":        32,
                    "os_type":            "rhel-9",
                    "container_cpu_cores":2.0,
                    "container_ram_gb":   4.0,
                    "container_type":     "web",
                    "rootless":           True,
                    "cgroup_version":     "v2",
                    "use_quadlet":        True,
                    "network_mode":       "bridge",
                    "expected_pids":      512,
                    "shm_size_mb":        64,
                    "read_only_rootfs":   True,
                    "drop_all_caps":      True,
                },
                "new_database_container": {
                    "mode":               "new",
                    "host_cpu_cores":     8,
                    "host_ram_gb":        32,
                    "os_type":            "rhel-9",
                    "container_cpu_cores":4.0,
                    "container_ram_gb":   8.0,
                    "container_type":     "database",
                    "rootless":           False,
                    "cgroup_version":     "v2",
                    "use_quadlet":        True,
                    "network_mode":       "host",
                    "expected_pids":      1024,
                    "shm_size_mb":        512,
                    "read_only_rootfs":   False,
                    "drop_all_caps":      True,
                },
                "existing_audit": {
                    "mode":               "existing",
                    "host_cpu_cores":     8,
                    "host_ram_gb":        32,
                    "os_type":            "rhel-9",
                    "container_cpu_cores":2.0,
                    "container_ram_gb":   4.0,
                    "container_type":     "web",
                    "rootless":           False,
                    "cgroup_version":     "v1",
                    "use_quadlet":        False,
                    "network_mode":       "bridge",
                    "expected_pids":      512,
                    "shm_size_mb":        64,
                    "read_only_rootfs":   False,
                    "drop_all_caps":      False,
                    "existing": {
                        "cpu_shares":            1024,
                        "cpus":                  None,
                        "memory_mb":             None,
                        "memory_swap_mb":        -1,
                        "memory_reservation_mb": None,
                        "pids_limit":            -1,
                        "ulimit_nofile":         "1024:1024",
                        "restart_policy":        "no",
                        "rootless":              False,
                        "security_opt":          [],
                        "cgroup_v2":             False,
                        "shm_size_mb":           64,
                        "oom_score_adj":         0,
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class PodmanOutput(BaseModel):
    """Full Podman calculator response."""
    mode:                    CalcMode

    # ── calculated values ──
    cpu_quota:               int    # microseconds per period
    cpu_period:              int    # microseconds (default 100000)
    memory_limit_mb:         int
    memory_swap_limit_mb:    int
    memory_reservation_mb:   int
    pids_limit:              int
    ulimit_nofile_soft:      int
    ulimit_nofile_hard:      int
    shm_size_mb:             int

    # ── ready-to-use config ──
    podman_run_flags:        str    # complete podman run flag block
    quadlet_unit:            str    # systemd .container quadlet unit

    # ── tiered params ──
    major_params:            list[TuningParam]
    medium_params:           list[TuningParam]
    minor_params:            list[TuningParam]

    # ── host OS tuning ──
    os_sysctl_conf:          str

    # ── advisory outputs ──
    ha_suggestions:          list[str]
    performance_warnings:    list[str]
    capacity_warning:        str | None

    # ── EXISTING mode only ──
    audit_findings:          list[str] = []
