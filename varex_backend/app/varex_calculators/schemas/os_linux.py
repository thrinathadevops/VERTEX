"""
app/schemas/os_linux.py
=======================
Pydantic schemas for the Linux OS standalone tuning calculator.

This module covers bare-metal / VM OS-level tuning independent of any
middleware. Parameters span:
  - Kernel networking (tcp, udp, socket buffers, conntrack)
  - Virtual memory (swappiness, dirty pages, hugepages)
  - File descriptors (system-wide + per-process)
  - CPU scheduler (NUMA, IRQ affinity, cgroup v2)
  - Disk I/O (scheduler, read-ahead, dirty writeback)
  - Security (ASLR, core dumps, kptr_restrict)
  - systemd (DefaultLimitNOFILE, CPUAccounting)

Three models:
  OSLinuxExisting  — current sysctl + ulimit values for EXISTING mode audit
  OSLinuxInput     — request body
  OSLinuxOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.varex_calculators.core.enums import OSType, CalcMode
from app.varex_calculators.core.models import TuningParam


# ── existing values (EXISTING mode only) ─────────────────────────────────
class OSLinuxExisting(BaseModel):
    """Current sysctl / ulimit / kernel parameter values. All optional."""
    # ── networking ──
    net_core_somaxconn:              str | None = None   # net.core.somaxconn
    net_core_netdev_max_backlog:     str | None = None
    net_ipv4_tcp_max_syn_backlog:    str | None = None
    net_ipv4_tcp_fin_timeout:        str | None = None
    net_ipv4_tcp_tw_reuse:           str | None = None
    net_ipv4_tcp_keepalive_time:     str | None = None
    net_ipv4_tcp_keepalive_intvl:    str | None = None
    net_ipv4_tcp_keepalive_probes:   str | None = None
    net_core_rmem_max:               str | None = None
    net_core_wmem_max:               str | None = None
    net_ipv4_tcp_rmem:               str | None = None
    net_ipv4_tcp_wmem:               str | None = None
    net_ipv4_ip_local_port_range:    str | None = None
    net_nf_conntrack_max:            str | None = None
    net_ipv4_tcp_syncookies:         str | None = None

    # ── virtual memory ──
    vm_swappiness:                   str | None = None
    vm_dirty_ratio:                  str | None = None
    vm_dirty_background_ratio:       str | None = None
    vm_overcommit_memory:            str | None = None
    vm_max_map_count:                str | None = None
    vm_nr_hugepages:                 str | None = None
    transparent_hugepage:            str | None = None   # always/madvise/never

    # ── file descriptors ──
    fs_file_max:                     str | None = None
    fs_nr_open:                      str | None = None
    ulimit_nofile_soft:              str | None = None
    ulimit_nofile_hard:              str | None = None
    systemd_default_limit_nofile:    str | None = None

    # ── CPU / scheduler ──
    kernel_sched_migration_cost_ns:  str | None = None
    kernel_numa_balancing:           str | None = None
    kernel_pid_max:                  str | None = None
    kernel_perf_event_paranoid:      str | None = None

    # ── disk I/O ──
    io_scheduler:                    str | None = None   # mq-deadline/none/bfq
    read_ahead_kb:                   str | None = None

    # ── security ──
    kernel_randomize_va_space:       str | None = None
    kernel_core_pattern:             str | None = None
    kernel_kptr_restrict:            str | None = None
    kernel_dmesg_restrict:           str | None = None


# ── request input ─────────────────────────────────────────────────────────
class OSLinuxInput(BaseModel):
    """
    Hardware + workload parameters for Linux OS tuning.

    mode
        new      → generate full sysctl.conf + limits.conf + systemd overrides
        existing → audit current OS parameters and return safe upgrade plan

    cpu_cores             : vCPU count
    ram_gb                : total RAM (GB)
    os_type               : Linux distribution variant
    workload_role         : primary workload on this host — drives tuning profile
                            web-server     → high connection count, socket buffers
                            database       → huge pages, dirty writeback, low swappiness
                            cache          → huge pages, vm.overcommit=1, no swap
                            container-host → conntrack, cgroup v2, pid_max
                            batch          → CPU scheduler, NUMA, I/O scheduler
                            general        → balanced profile
    disk_type             : ssd / nvme / hdd — drives I/O scheduler and read-ahead
    network_speed_gbps    : NIC speed (1/10/25/40/100 Gbps) — drives socket buffers
    numa_nodes            : number of NUMA nodes (affects scheduling params)
    enable_hugepages      : allocate transparent/static hugepages
    hugepage_size_gb      : GB to reserve for 2MB hugepages
    expected_connections  : peak simultaneous TCP connections
    """
    mode:                 CalcMode = CalcMode.NEW

    cpu_cores:            Annotated[int,   Field(ge=1,   le=1024)]
    ram_gb:               Annotated[float, Field(gt=0,   le=4096)]
    os_type:              OSType   = OSType.RHEL_9
    workload_role:        Literal[
                              "web-server", "database", "cache",
                              "container-host", "batch", "general"
                          ] = "general"
    disk_type:            Literal["ssd", "nvme", "hdd"] = "ssd"
    network_speed_gbps:   Literal[1, 10, 25, 40, 100] = 10
    numa_nodes:           Annotated[int,   Field(ge=1,   le=256, default=1)]
    enable_hugepages:     bool = False
    hugepage_size_gb:     Annotated[float, Field(ge=0,   le=2048, default=0.0)]
    expected_connections: Annotated[int,   Field(ge=1,   default=10_000)]
    existing:             OSLinuxExisting = Field(default_factory=OSLinuxExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_web_server": {
                    "mode":                "new",
                    "cpu_cores":           8,
                    "ram_gb":              32,
                    "os_type":             "rhel-9",
                    "workload_role":       "web-server",
                    "disk_type":           "ssd",
                    "network_speed_gbps":  10,
                    "numa_nodes":          1,
                    "enable_hugepages":    False,
                    "hugepage_size_gb":    0,
                    "expected_connections":50000,
                },
                "new_database": {
                    "mode":                "new",
                    "cpu_cores":           16,
                    "ram_gb":              128,
                    "os_type":             "rhel-9",
                    "workload_role":       "database",
                    "disk_type":           "nvme",
                    "network_speed_gbps":  25,
                    "numa_nodes":          2,
                    "enable_hugepages":    True,
                    "hugepage_size_gb":    32,
                    "expected_connections":10000,
                },
                "existing_audit": {
                    "mode":                "existing",
                    "cpu_cores":           8,
                    "ram_gb":              32,
                    "os_type":             "rhel-9",
                    "workload_role":       "web-server",
                    "disk_type":           "ssd",
                    "network_speed_gbps":  10,
                    "numa_nodes":          1,
                    "enable_hugepages":    False,
                    "hugepage_size_gb":    0,
                    "expected_connections":50000,
                    "existing": {
                        "net_core_somaxconn":           "128",
                        "net_ipv4_tcp_max_syn_backlog":  "512",
                        "net_ipv4_tcp_fin_timeout":      "60",
                        "net_ipv4_tcp_tw_reuse":         "0",
                        "vm_swappiness":                 "60",
                        "vm_dirty_ratio":                "20",
                        "vm_max_map_count":              "65530",
                        "fs_file_max":                   "65536",
                        "ulimit_nofile_soft":            "1024",
                        "ulimit_nofile_hard":            "1024",
                        "kernel_randomize_va_space":     "0",
                        "kernel_pid_max":                "32768",
                        "transparent_hugepage":          "always",
                        "io_scheduler":                  "cfq",
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class OSLinuxOutput(BaseModel):
    """Full Linux OS calculator response."""
    mode:                      CalcMode

    # ── key calculated values ──
    somaxconn:                 int
    tcp_max_syn_backlog:       int
    rmem_max:                  int
    wmem_max:                  int
    file_max:                  int
    nofile_soft:               int
    nofile_hard:               int
    nr_hugepages:              int
    pid_max:                   int

    # ── ready-to-use config files ──
    sysctl_conf:               str   # /etc/sysctl.d/99-varex.conf
    limits_conf:               str   # /etc/security/limits.d/99-varex.conf
    systemd_override:          str   # /etc/systemd/system.conf.d/99-varex.conf
    tuned_profile:             str   # /etc/tuned/varex/tuned.conf
    apply_script:              str   # bash script to apply all settings

    # ── tiered params ──
    major_params:              list[TuningParam]
    medium_params:             list[TuningParam]
    minor_params:              list[TuningParam]

    # ── advisory ──
    ha_suggestions:            list[str]
    performance_warnings:      list[str]
    capacity_warning:          str | None

    # ── EXISTING mode only ──
    audit_findings:            list[str] = []


