"""
app/api/v1/os_linux.py
======================
FastAPI router for the Linux OS standalone tuning calculator.

Endpoints
---------
POST /api/v1/os-linux/calculate
    mode=new      → generate sysctl.conf + limits.conf + systemd override + tuned profile + apply script
    mode=existing → audit current OS parameters

POST /api/v1/os-linux/example/new-web-server
    Pre-filled NEW mode — web server (NGINX/Apache), SSD, 10Gbps

POST /api/v1/os-linux/example/new-database
    Pre-filled NEW mode — database (PostgreSQL/MySQL), NVMe, hugepages

POST /api/v1/os-linux/example/existing
    Pre-filled EXISTING audit — default kernel params, ASLR off, THP=always
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.os_linux import OSLinuxInput, OSLinuxOutput
from app.calculators.os_linux_calculator import OSLinuxCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=OSLinuxOutput,
    summary="OS Linux – Full kernel + FD + VM + I/O tuning (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware + workload specs, receive:
- `somaxconn` = `min(max(expected_connections, 65535), 1048576)`
- `rmem_max / wmem_max` = `min(RAM × 2%, 128–256MB)` (NIC-speed scaled)
- `fs.file-max` = `max(connections × 10, cpu_cores × 200000, 2097152)`
- `ulimit nofile` = `min(file_max, 1048576)`
- `kernel.pid_max` = `min(max(cpu_cores × 32768, 131072), 4194304)`
- `vm.swappiness`: database/cache=1, web=10, general=20
- `vm.dirty_ratio`: database/NVMe=5, database/HDD=10, others=20
- I/O scheduler: NVMe=none, SSD=mq-deadline, HDD=bfq
- Read-ahead: NVMe=0KB, SSD=128KB, HDD=4096KB
- THP: database/cache=never, others=madvise
- nf_conntrack_max = `max(connections × 4, 262144)`
- NUMA: numa_balancing=1 + sched_migration_cost if numa_nodes > 1

**Five output files:**
- `sysctl_conf`      → `/etc/sysctl.d/99-varex.conf`
- `limits_conf`      → `/etc/security/limits.d/99-varex.conf`
- `systemd_override` → `/etc/systemd/system.conf.d/99-varex.conf`
- `tuned_profile`    → `/etc/tuned/varex/tuned.conf`
- `apply_script`     → bash script to apply all settings atomically

**EXISTING mode** — audit current kernel params:
- `somaxconn=128` (kernel default — exhausted at 129th connection)
- `ulimit nofile=1024` (Linux default — fails at 513th FD)
- `vm.swappiness=60` for database (catastrophic swap)
- `kernel.randomize_va_space=0` (ASLR disabled — security critical)
- `transparent_hugepage=always` for database (10-100ms compaction stalls)
- `io_scheduler=cfq` (removed in kernel 5.0+)
- `kernel.pid_max=32768` (default — exhausted by JVM thread pools)
    """,
)
def calculate_os_linux(inp: OSLinuxInput) -> OSLinuxOutput:
    try:
        result = OSLinuxCalculator(inp).generate()
        logger.info(
            "OS Linux calculate",
            extra={
                "mode":           inp.mode.value,
                "workload_role":  inp.workload_role,
                "cpu_cores":      inp.cpu_cores,
                "ram_gb":         inp.ram_gb,
                "disk_type":      inp.disk_type,
                "net_gbps":       inp.network_speed_gbps,
                "somaxconn":      result.somaxconn,
                "file_max":       result.file_max,
                "nofile":         result.nofile_hard,
                "hugepages":      result.nr_hugepages,
                "audit_count":    len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("OS Linux validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new-web-server",
    summary="OS Linux – Example NEW mode (web server, SSD, 10Gbps)",
    include_in_schema=True,
)
def os_linux_example_new_web() -> JSONResponse:
    return JSONResponse({
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
    })


@router.post(
    "/example/new-database",
    summary="OS Linux – Example NEW mode (database, NVMe, hugepages, NUMA)",
    include_in_schema=True,
)
def os_linux_example_new_database() -> JSONResponse:
    """
    Database OS tuning:
    - vm.swappiness=1 (near-zero swap)
    - THP=never (no compaction stalls)
    - dirty_ratio=5 (frequent flush, small data loss window)
    - io_scheduler=none (NVMe — bypass kernel scheduler)
    - hugepages: 32GB reserved for PostgreSQL shared_buffers
    - NUMA: 2 nodes, numa_balancing=1
    """
    return JSONResponse({
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
    })


@router.post(
    "/example/existing",
    summary="OS Linux – Example EXISTING mode audit (kernel defaults + common misconfigs)",
    include_in_schema=True,
)
def os_linux_example_existing() -> JSONResponse:
    """
    Common Linux default misconfigs:
    - somaxconn=128 (kernel default — drops at 129th TCP connection)
    - tcp_max_syn_backlog=512 (default — SYN flood vulnerability)
    - tcp_fin_timeout=60 (default — stale socket pile-up)
    - tcp_tw_reuse=0 (default — TIME_WAIT port exhaustion)
    - vm.swappiness=60 (default — aggressively swaps production workloads)
    - fs.file-max=65536 (default — exhausted by NGINX at 33K connections)
    - ulimit nofile=1024 (Linux default — fails at 513th connection)
    - kernel.randomize_va_space=0 (ASLR off — security critical)
    - transparent_hugepage=always (THP compaction stalls)
    - io_scheduler=cfq (removed in kernel 5.0+)
    - kernel.pid_max=32768 (default — exhausted by JVM thread pools)
    - vm.max_map_count=65530 (default — Elasticsearch fails to start)
    """
    return JSONResponse({
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
            "kernel_pid_max":               "32768",
            "transparent_hugepage":          "always",
            "io_scheduler":                  "cfq",
        },
    })
