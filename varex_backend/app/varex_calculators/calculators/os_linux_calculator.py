"""
app/calculators/os_linux_calculator.py
========================================
Linux OS standalone tuning calculator — NEW and EXISTING modes.

Formulas
--------
somaxconn           = min(max(expected_connections, 65535), 1048576)
tcp_max_syn_backlog = somaxconn
netdev_max_backlog  = somaxconn * 2
rmem_max / wmem_max = min(RAM_bytes * 2%, 256MB)  → network_speed scaled
  10 Gbps: min(RAM*2%, 128MB)
  25+Gbps: min(RAM*2%, 256MB)
tcp rmem/wmem       = [4096, 87380, rmem_max]

file_max            = max(expected_connections * 10, cpu_cores * 200000, 2097152)
nofile              = min(file_max, 1048576)

nr_hugepages        = (hugepage_size_gb * 1024) / 2  (2MB hugepages)
pid_max             = min(max(cpu_cores * 32768, 131072), 4194304)

vm.swappiness:
  database / cache  → 1   (near-zero swap, never evict working set)
  web-server        → 10
  container-host    → 10
  batch / general   → 20

vm.dirty_ratio:
  database (NVMe)   → 5   (flush often, minimize data loss window)
  database (HDD)    → 10
  web-server        → 20
  general           → 20

I/O scheduler:
  NVMe → none (noop — kernel queue, no extra scheduling)
  SSD  → mq-deadline
  HDD  → bfq (Budget Fair Queueing)

Read-ahead:
  NVMe → 0    (PCIe latency so low, read-ahead adds overhead)
  SSD  → 128  (128KB — small random reads benefit minimally)
  HDD  → 4096 (4MB — sequential prefetch critical for HDD)

NUMA:
  numa_nodes > 1 → kernel.numa_balancing=1, sched_migration_cost_ns=500000
  numa_nodes = 1 → numa_balancing=0 (overhead without benefit)
"""
from __future__ import annotations

import math

from app.varex_calculators.calculators.base import BaseCalculator
from app.varex_calculators.core.enums import ImpactLevel, CalcMode
from app.varex_calculators.schemas.os_linux import OSLinuxInput, OSLinuxOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class OSLinuxCalculator(BaseCalculator):

    def __init__(self, inp: OSLinuxInput) -> None:
        self._require_positive(inp.cpu_cores, "cpu_cores")
        self._require_positive(inp.ram_gb,    "ram_gb")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _somaxconn(self) -> int:
        return min(max(self.inp.expected_connections, 65535), 1_048_576)

    def _rmem_max(self) -> int:
        ram_bytes = int(self.inp.ram_gb * 1024 * 1024 * 1024)
        cap = 268_435_456 if self.inp.network_speed_gbps >= 25 else 134_217_728
        return min(int(ram_bytes * 0.02), cap)

    def _file_max(self) -> int:
        return max(
            self.inp.expected_connections * 10,
            self.inp.cpu_cores * 200_000,
            2_097_152,
        )

    def _nofile(self) -> int:
        return min(self._file_max(), 1_048_576)

    def _nr_hugepages(self) -> int:
        if not self.inp.enable_hugepages or self.inp.hugepage_size_gb <= 0:
            return 0
        return int(self.inp.hugepage_size_gb * 1024 / 2)   # 2MB pages

    def _pid_max(self) -> int:
        return min(max(self.inp.cpu_cores * 32_768, 131_072), 4_194_304)

    def _swappiness(self) -> int:
        return {
            "database":       1,
            "cache":          1,
            "web-server":     10,
            "container-host": 10,
            "batch":          20,
            "general":        20,
        }.get(self.inp.workload_role, 20)

    def _dirty_ratio(self) -> tuple[int, int]:
        """Returns (dirty_ratio, dirty_background_ratio)."""
        if self.inp.workload_role == "database":
            return (5, 2) if self.inp.disk_type == "nvme" else (10, 5)
        if self.inp.workload_role in ("cache",):
            return (10, 3)
        return (20, 10)

    def _io_scheduler(self) -> str:
        return {"nvme": "none", "ssd": "mq-deadline", "hdd": "bfq"}.get(
            self.inp.disk_type, "mq-deadline"
        )

    def _read_ahead_kb(self) -> int:
        return {"nvme": 0, "ssd": 128, "hdd": 4096}.get(self.inp.disk_type, 128)

    def _overcommit(self) -> int:
        """vm.overcommit_memory: 0=heuristic, 1=always(cache), 2=never(database)."""
        return {
            "cache":    1,
            "database": 2,
        }.get(self.inp.workload_role, 0)

    def _conntrack_max(self) -> int:
        return max(self.inp.expected_connections * 4, 262_144)

    # ── config file renderers ─────────────────────────────────────────────────

    def _render_sysctl(self) -> str:
        inp       = self.inp
        somax     = self._somaxconn()
        rmem      = self._rmem_max()
        fmax      = self._file_max()
        pid_max   = self._pid_max()
        swap      = self._swappiness()
        dr, dbr   = self._dirty_ratio()
        hp        = self._nr_hugepages()
        overcom   = self._overcommit()
        ctmax     = self._conntrack_max()
        port_hi   = 65535
        port_lo   = 1024

        tcp_rmem  = f"4096 87380 {rmem}"
        tcp_wmem  = f"4096 65536 {rmem}"

        numa_block = (
            "# ── NUMA scheduler ──────────────────────────────────────────────
"
            "kernel.numa_balancing = 1
"
            "kernel.sched_migration_cost_ns = 500000
"
            "kernel.sched_autogroup_enabled = 0
"
        ) if inp.numa_nodes > 1 else (
            "# ── NUMA (single node — balancing disabled) ─────────────────────
"
            "kernel.numa_balancing = 0
"
        )

        hugepage_block = (
            f"# ── Huge pages ({inp.hugepage_size_gb}GB reserved) ─────────────────────────
"
            f"vm.nr_hugepages = {hp}
"
            "vm.hugetlb_shm_group = 0
"
        ) if inp.enable_hugepages and hp > 0 else (
            "# ── Huge pages (disabled) ───────────────────────────────────────
"
            "# vm.nr_hugepages = 0
"
        )

        thp = "never" if inp.workload_role == "database" else "madvise"

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Linux OS sysctl  [{inp.mode.value.upper():8s}]  "
            f"role={inp.workload_role}  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Location: /etc/sysctl.d/99-varex.conf
"
            f"# Apply:    sysctl -p /etc/sysctl.d/99-varex.conf

"
            f"# ── TCP connection backlog ───────────────────────────────────────
"
            f"net.core.somaxconn = {somax}
"
            f"net.core.netdev_max_backlog = {somax * 2}
"
            f"net.ipv4.tcp_max_syn_backlog = {somax}

"
            f"# ── Socket buffers (NIC={inp.network_speed_gbps}Gbps) ────────────────────────
"
            f"net.core.rmem_default = 262144
"
            f"net.core.wmem_default = 262144
"
            f"net.core.rmem_max = {rmem}
"
            f"net.core.wmem_max = {rmem}
"
            f"net.core.optmem_max = 65536
"
            f"net.ipv4.tcp_rmem = {tcp_rmem}
"
            f"net.ipv4.tcp_wmem = {tcp_wmem}
"
            f"net.ipv4.udp_rmem_min = 8192
"
            f"net.ipv4.udp_wmem_min = 8192

"
            f"# ── TCP tuning ───────────────────────────────────────────────────
"
            f"net.ipv4.tcp_fin_timeout = 15
"
            f"net.ipv4.tcp_tw_reuse = 1
"
            f"net.ipv4.tcp_keepalive_time = 300
"
            f"net.ipv4.tcp_keepalive_intvl = 30
"
            f"net.ipv4.tcp_keepalive_probes = 5
"
            f"net.ipv4.tcp_syncookies = 1
"
            f"net.ipv4.tcp_max_tw_buckets = 2000000
"
            f"net.ipv4.ip_local_port_range = {port_lo} {port_hi}
"
            f"net.ipv4.tcp_slow_start_after_idle = 0
"
            f"net.ipv4.tcp_mtu_probing = 1
"
            f"net.ipv4.tcp_sack = 1
"
            f"net.ipv4.tcp_dsack = 1
"
            f"net.ipv4.tcp_timestamps = 1
"
            f"net.ipv4.tcp_window_scaling = 1
"
            f"net.ipv4.tcp_moderate_rcvbuf = 1

"
            f"# ── Conntrack (for container-host / NAT) ─────────────────────────
"
            f"net.nf_conntrack_max = {ctmax}
"
            f"net.netfilter.nf_conntrack_tcp_timeout_established = 300
"
            f"net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30

"
            f"# ── File descriptors ─────────────────────────────────────────────
"
            f"fs.file-max = {fmax}
"
            f"fs.nr_open = {fmax}
"
            f"fs.inotify.max_user_watches = 524288
"
            f"fs.inotify.max_user_instances = 8192

"
            f"# ── Virtual memory ───────────────────────────────────────────────
"
            f"vm.swappiness = {swap}
"
            f"vm.dirty_ratio = {dr}
"
            f"vm.dirty_background_ratio = {dbr}
"
            f"vm.dirty_expire_centisecs = 3000
"
            f"vm.dirty_writeback_centisecs = 500
"
            f"vm.overcommit_memory = {overcom}
"
            f"vm.max_map_count = 1048576
"
            f"vm.min_free_kbytes = {max(65536, int(inp.ram_gb * 1024 * 0.01))}

"
            f"{hugepage_block}
"
            f"# ── Transparent Huge Pages ───────────────────────────────────────
"
            f"# Set at runtime (sysctl doesn't control THP — use tuned or rc.local):
"
            f"# echo {thp} > /sys/kernel/mm/transparent_hugepage/enabled
"
            f"# echo {thp} > /sys/kernel/mm/transparent_hugepage/defrag

"
            f"# ── Kernel / process ─────────────────────────────────────────────
"
            f"kernel.pid_max = {pid_max}
"
            f"kernel.threads-max = {pid_max * 2}
"
            f"kernel.perf_event_paranoid = 2
"
            f"kernel.kptr_restrict = 2
"
            f"kernel.dmesg_restrict = 1
"
            f"kernel.randomize_va_space = 2
"
            f"kernel.core_pattern = |/usr/lib/systemd/systemd-coredump %P %u %g %s %t %c %h
"
            f"kernel.core_uses_pid = 1

"
            f"{numa_block}
"
            f"# ── Security ─────────────────────────────────────────────────────
"
            f"net.ipv4.conf.all.rp_filter = 1
"
            f"net.ipv4.conf.default.rp_filter = 1
"
            f"net.ipv4.icmp_echo_ignore_broadcasts = 1
"
            f"net.ipv4.conf.all.accept_source_route = 0
"
            f"net.ipv4.conf.default.accept_source_route = 0
"
            f"net.ipv4.conf.all.send_redirects = 0
"
            f"net.ipv4.conf.default.send_redirects = 0
"
        )

    def _render_limits_conf(self) -> str:
        nf = self._nofile()
        pid = self._pid_max()
        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX /etc/security/limits.d/99-varex.conf                 ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Apply: re-login or 'ulimit -n {nf}' in shell

"
            f"# ── All users ──────────────────────────────────────────────────
"
            f"*    soft    nofile      {nf}
"
            f"*    hard    nofile      {nf}
"
            f"*    soft    nproc       {pid}
"
            f"*    hard    nproc       {pid}
"
            f"*    soft    stack       65536
"
            f"*    hard    stack       65536
"
            f"*    soft    core        unlimited
"
            f"*    hard    core        unlimited

"
            f"# ── Root ───────────────────────────────────────────────────────
"
            f"root soft    nofile      {nf}
"
            f"root hard    nofile      {nf}
"
        )

    def _render_systemd_override(self) -> str:
        nf = self._nofile()
        pid = self._pid_max()
        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX /etc/systemd/system.conf.d/99-varex.conf             ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Apply: systemctl daemon-reexec

"
            f"[Manager]
"
            f"DefaultLimitNOFILE={nf}
"
            f"DefaultLimitNPROC={pid}
"
            f"DefaultLimitCORE=infinity
"
            f"DefaultTasksMax={pid}
"
            f"DefaultLimitSTACK=65536
"
            f"CPUAccounting=yes
"
            f"MemoryAccounting=yes
"
            f"TasksAccounting=yes
"
            f"IOAccounting=yes
"
        )

    def _render_tuned_profile(self) -> str:
        inp       = self.inp
        somax     = self._somaxconn()
        rmem      = self._rmem_max()
        swap      = self._swappiness()
        dr, dbr   = self._dirty_ratio()
        sched     = self._io_scheduler()
        ra        = self._read_ahead_kb()
        pid_max   = self._pid_max()
        fmax      = self._file_max()
        hp        = self._nr_hugepages()
        thp       = "never" if inp.workload_role == "database" else "madvise"

        base_profile = {
            "web-server":     "throughput-performance",
            "database":       "latency-performance",
            "cache":          "latency-performance",
            "container-host": "throughput-performance",
            "batch":          "throughput-performance",
            "general":        "balanced",
        }.get(inp.workload_role, "balanced")

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX tuned profile: /etc/tuned/varex/tuned.conf           ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Activate: tuned-adm profile varex
"
            f"# Verify:   tuned-adm active

"
            f"[main]
"
            f"summary=VAREX optimised for {inp.workload_role} "
            f"(RAM={inp.ram_gb}GB CPU={inp.cpu_cores} disk={inp.disk_type})
"
            f"include={base_profile}

"
            f"[sysctl]
"
            f"net.core.somaxconn = {somax}
"
            f"net.core.rmem_max = {rmem}
"
            f"net.core.wmem_max = {rmem}
"
            f"vm.swappiness = {swap}
"
            f"vm.dirty_ratio = {dr}
"
            f"vm.dirty_background_ratio = {dbr}
"
            f"vm.max_map_count = 1048576
"
            f"kernel.pid_max = {pid_max}
"
            f"fs.file-max = {fmax}
"
            + (f"vm.nr_hugepages = {hp}
" if hp > 0 else "") +
            f"
[disk]
"
            f"elevator = {sched}
"
            f"readahead_kb = {ra}

"
            f"[vm]
"
            f"transparent_hugepages = {thp}

"
            f"[cpu]
"
            + (
                "governor = performance
"
                "energy_performance_preference = performance
"
                if inp.workload_role in ("database", "cache", "web-server") else
                "governor = ondemand
"
            )
        )

    def _render_apply_script(self) -> str:
        inp    = self.inp
        sched  = self._io_scheduler()
        ra     = self._read_ahead_kb()
        thp    = "never" if inp.workload_role == "database" else "madvise"

        return (
            f"#!/usr/bin/env bash
"
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Linux OS apply script  [{inp.mode.value.upper():8s}]  "
            f"role={inp.workload_role}  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Run as root: bash apply_varex_os.sh
"
            f"set -euo pipefail

"
            f"echo '[VAREX] Applying sysctl...'
"
            f"sysctl -p /etc/sysctl.d/99-varex.conf

"
            f"echo '[VAREX] Applying file descriptor limits...'
"
            f"# limits.conf changes take effect on next login
"
            f"# For running services, apply via systemd override:
"
            f"mkdir -p /etc/systemd/system.conf.d
"
            f"cp /etc/systemd/system.conf.d/99-varex.conf /etc/systemd/system.conf.d/99-varex.conf
"
            f"systemctl daemon-reexec

"
            f"echo '[VAREX] Applying I/O scheduler ({sched})...'
"
            f"for dev in $(ls /sys/block | grep -v loop); do
"
            f"  if [ -f /sys/block/$dev/queue/scheduler ]; then
"
            f"    echo '{sched}' > /sys/block/$dev/queue/scheduler && \
"
            f"      echo "  Set $dev scheduler={sched}"
"
            f"  fi
"
            f"  if [ -f /sys/block/$dev/queue/read_ahead_kb ]; then
"
            f"    echo '{ra}' > /sys/block/$dev/queue/read_ahead_kb && \
"
            f"      echo "  Set $dev read_ahead_kb={ra}"
"
            f"  fi
"
            f"done

"
            f"echo '[VAREX] Setting Transparent Huge Pages = {thp}...'
"
            f"echo '{thp}' > /sys/kernel/mm/transparent_hugepage/enabled
"
            f"echo '{thp}' > /sys/kernel/mm/transparent_hugepage/defrag

"
            + (
                f"echo '[VAREX] Applying tuned profile...'
"
                f"mkdir -p /etc/tuned/varex
"
                f"cp tuned.conf /etc/tuned/varex/tuned.conf
"
                f"tuned-adm profile varex

"
            ) +
            f"echo '[VAREX] Done. Verify with:'
"
            f"echo '  sysctl net.core.somaxconn fs.file-max vm.swappiness'
"
            f"echo '  cat /proc/sys/kernel/pid_max'
"
            f"echo '  ulimit -n  (in new shell after re-login)'
"
        )

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self) -> list:
        inp    = self.inp
        p      = self._p
        ex     = inp.existing
        somax  = self._somaxconn()
        rmem   = self._rmem_max()
        fmax   = self._file_max()
        nf     = self._nofile()
        pid    = self._pid_max()
        swap   = self._swappiness()
        dr,dbr = self._dirty_ratio()
        sched  = self._io_scheduler()
        ra     = self._read_ahead_kb()
        hp     = self._nr_hugepages()
        oc     = self._overcommit()
        ctmax  = self._conntrack_max()

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "net.core.somaxconn", str(somax), M,
                f"TCP accept queue = {somax}. "
                "Default 128 (RHEL 7) / 4096 (RHEL 9) — both too low for production. "
                "When accept queue full: kernel drops new TCP SYN silently (SYN cookies if enabled). "
                f"Formula: min(max(expected_connections({inp.expected_connections}), 65535), 1048576). "
                "Apache/NGINX listen backlog must also match: --backlog={somax}.",
                f"net.core.somaxconn = {somax}",
                ex.net_core_somaxconn,
                safe=False,
            ),
            p(
                "net.ipv4.tcp_max_syn_backlog", str(somax), M,
                f"SYN half-open connection queue = {somax}. "
                "Separate from somaxconn — handles incomplete 3-way handshakes. "
                "SYN flood: without syncookies, this queue fills first. "
                "Set = somaxconn to avoid asymmetry.",
                f"net.ipv4.tcp_max_syn_backlog = {somax}",
                ex.net_ipv4_tcp_max_syn_backlog,
                safe=False,
            ),
            p(
                "fs.file-max", str(fmax), M,
                f"System-wide file descriptor limit = {fmax:,}. "
                "Default 65536 — exhausted by a single busy NGINX instance. "
                f"Formula: max(connections×10, cpu_cores×200000, 2097152) = {fmax:,}. "
                "Each: TCP socket, file handle, epoll FD, inotify watch = 1 FD. "
                "Exhaustion: 'Too many open files in system' — affects ALL processes.",
                f"fs.file-max = {fmax}
fs.nr_open = {fmax}",
                ex.fs_file_max,
                safe=False,
            ),
            p(
                "ulimit nofile (per-process)", f"{nf}:{nf}", M,
                f"Per-process FD limit = {nf:,}. "
                "Default 1024 (soft) — hit by any production web server at ~513 connections. "
                "Set in /etc/security/limits.d/ AND systemd DefaultLimitNOFILE. "
                "Two places required: limits.conf applies to PAM login sessions; "
                "systemd override applies to all systemd-managed services. "
                "Verify: cat /proc/<PID>/limits | grep 'open files'",
                f"*  soft  nofile  {nf}
*  hard  nofile  {nf}
"
                f"# AND systemd: DefaultLimitNOFILE={nf}",
                f"{ex.ulimit_nofile_soft}:{ex.ulimit_nofile_hard}"
                if ex.ulimit_nofile_soft else None,
                safe=False,
            ),
            p(
                "vm.swappiness", str(swap), M,
                f"Swap aggressiveness = {swap}. "
                + {
                    1:  "Near-zero swap. Kernel only swaps under extreme memory pressure. "
                        "Critical for database/cache: swapped pages cause 1000× latency spikes. "
                        "Value=1 (not 0): value=0 can cause OOM kill loop in kernel < 3.5.",
                    10: "Low swappiness. File cache preferred over swap. "
                        "Good for web servers: anonymous memory (heap) rarely swapped.",
                    20: "Moderate. Kernel balances file cache vs swap. Default=60 is too aggressive.",
                }.get(swap, f"swappiness={swap}."),
                f"vm.swappiness = {swap}",
                ex.vm_swappiness,
                safe=False,
            ),
            p(
                "kernel.pid_max", str(pid), M,
                f"Max PIDs = {pid:,} = min(max(cpu_cores×32768, 131072), 4194304). "
                "Default 32768 — exhausted by: JVM (creates ~100 threads/app), "
                "container hosts (each container fork adds PIDs), batch jobs. "
                "PID exhaustion: fork() fails with EAGAIN — unrecoverable without reboot. "
                "Monitor: cat /proc/sys/kernel/pid_max vs awk '{print $1}' /proc/sys/kernel/nr_threads",
                f"kernel.pid_max = {pid}",
                ex.kernel_pid_max,
                safe=False,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "net.core.rmem_max / wmem_max", f"{rmem:,}", MED,
                f"Max socket receive/send buffer = {rmem:,} bytes. "
                f"Formula: min(RAM × 2%, {'256MB' if inp.network_speed_gbps >= 25 else '128MB'}). "
                f"At {inp.network_speed_gbps}Gbps NIC: "
                f"BDP = {inp.network_speed_gbps}Gbps × 100ms RTT = "
                f"{int(inp.network_speed_gbps * 1e9 / 8 * 0.1):,} bytes. "
                "Buffer must be ≥ BDP to saturate NIC. "
                "Default 212992 bytes = 1.7 Mbps at 100ms RTT — NIC underutilised.",
                f"net.core.rmem_max = {rmem}
net.core.wmem_max = {rmem}",
                ex.net_core_rmem_max,
            ),
            p(
                "net.ipv4.tcp_fin_timeout", "15", MED,
                "FIN_WAIT2 socket timeout = 15s. "
                "Default 60s: each closed connection holds socket state for 60s. "
                "At 10,000 connections/sec: 600,000 FIN_WAIT2 sockets × 60s "
                "= 36M socket-seconds/min. "
                "Reduce to 15s: 4× faster socket reclamation. "
                "Below 10s: risks premature close of legitimate slow connections.",
                "net.ipv4.tcp_fin_timeout = 15",
                ex.net_ipv4_tcp_fin_timeout,
            ),
            p(
                "net.ipv4.tcp_tw_reuse", "1", MED,
                "TIME_WAIT socket reuse for outbound connections. "
                "Allows reuse of TIME_WAIT sockets for new connections to same remote. "
                "Critical for: reverse proxies (NGINX→backend), "
                "service mesh sidecar proxies (thousands of short-lived connections). "
                "Safe: only applies to outbound — does not affect inbound server sockets. "
                "Default 0: ephemeral port range exhaustion at high RPS.",
                "net.ipv4.tcp_tw_reuse = 1",
                ex.net_ipv4_tcp_tw_reuse,
            ),
            p(
                "vm.dirty_ratio / vm.dirty_background_ratio", f"{dr} / {dbr}", MED,
                f"dirty_ratio={dr}: process stalls on write when dirty pages exceed {dr}% RAM. "
                f"dirty_background_ratio={dbr}: pdflush starts writeback at {dbr}% RAM. "
                + (
                    f"Database: low ratios = frequent flushing = small data loss window on crash. "
                    f"NVMe: can absorb {dr}% flush bursts at >3GB/s write speed."
                    if inp.workload_role == "database" else
                    f"Web server: higher ratios = fewer flush stalls under write bursts."
                ),
                f"vm.dirty_ratio = {dr}
vm.dirty_background_ratio = {dbr}",
                ex.vm_dirty_ratio,
            ),
            p(
                "I/O scheduler", sched, MED,
                {
                    "none":        f"NVMe scheduler=none (noop). "
                                   "NVMe queues 64K+ IOPS internally via PCIe. "
                                   "Any Linux I/O scheduler adds overhead without benefit. "
                                   "none = bypass kernel scheduling, submit directly to NVMe queue.",
                    "mq-deadline": f"SSD scheduler=mq-deadline. "
                                   "Multi-queue deadline: prevents I/O starvation, "
                                   "groups reads (500ms deadline) and writes (5000ms deadline). "
                                   "Better than CFQ for SSDs: no rotational seek optimisation needed.",
                    "bfq":         f"HDD scheduler=bfq (Budget Fair Queueing). "
                                   "BFQ: assigns budgets to processes, rotational-aware scheduling. "
                                   "Reduces seek time, fair I/O distribution. "
                                   "Critical for HDD: CFQ (old default) causes throughput collapse.",
                }.get(sched, ""),
                f"echo '{sched}' > /sys/block/<dev>/queue/scheduler",
                ex.io_scheduler,
                safe=False,
            ),
            p(
                "Read-ahead", f"{ra}KB", MED,
                {
                    0:    "NVMe: read-ahead=0. PCIe latency so low that prefetching "
                          "adds overhead without benefit for random I/O workloads.",
                    128:  "SSD: read-ahead=128KB. Small sequential prefetch for "
                          "log files and sequential scans. Random I/O unaffected.",
                    4096: "HDD: read-ahead=4096KB (4MB). Sequential prefetch critical: "
                          "HDD rotational seek = 5-10ms. Prefetching avoids seek penalty "
                          "for log reads, sequential table scans.",
                }.get(ra, f"read-ahead={ra}KB"),
                f"echo '{ra}' > /sys/block/<dev>/queue/read_ahead_kb",
                ex.read_ahead_kb,
            ),
            p(
                "vm.max_map_count", "1048576", MED,
                "Max virtual memory areas per process = 1,048,576. "
                "Default 65530. "
                "Elasticsearch: requires ≥ 262144 for mmapped Lucene segments. "
                "JVM + NIO + container workloads: each mmap, shared lib, JIT code segment = 1 VMA. "
                "Exhaustion: mmap() fails with ENOMEM — JVM crash or Elasticsearch node exit.",
                "vm.max_map_count = 1048576",
                ex.vm_max_map_count,
            ),
            p(
                "Transparent Huge Pages (THP)",
                "never" if inp.workload_role == "database" else "madvise", MED,
                {
                    "database": (
                        "THP=never for databases. "
                        "THP khugepaged: collapses 4KB pages into 2MB — "
                        "causes 10-100ms latency spikes (memory compaction stall). "
                        "PostgreSQL / MySQL / MongoDB: THP is a known performance killer. "
                        "always → never reduces tail latency by 10× in DB workloads."
                    ),
                    "cache": (
                        "THP=never for Redis/Memcached. "
                        "Redis fork() (RDB snapshot) with THP: copy-on-write on 2MB pages "
                        "amplifies memory usage massively. Known Redis latency spike cause."
                    ),
                }.get(inp.workload_role,
                    "THP=madvise: only allocate hugepages when explicitly requested via madvise(). "
                    "JVM: uses madvise for heap → benefits from hugepages. "
                    "Avoids compaction stalls for non-madvise allocations."
                ),
                f"echo '{'never' if inp.workload_role in ('database','cache') else 'madvise'}' "
                f"> /sys/kernel/mm/transparent_hugepage/enabled",
                ex.transparent_hugepage,
                safe=False,
            ),
            p(
                "nf_conntrack_max", str(ctmax), MED,
                f"Netfilter connection tracking table = {ctmax:,} entries. "
                "Default 65536 — exhausted on busy NAT/container hosts. "
                "Exhaustion: kernel drops new connections silently with EPERM. "
                f"Formula: max(expected_connections×4, 262144) = {ctmax:,}. "
                "Also set: net.netfilter.nf_conntrack_tcp_timeout_established=300 "
                "(default 432000s = 5 days → 5 days of stale entries!).",
                f"net.nf_conntrack_max = {ctmax}
"
                "net.netfilter.nf_conntrack_tcp_timeout_established = 300",
                ex.net_nf_conntrack_max,
                safe=False,
            ),
        ]

        if inp.enable_hugepages and hp > 0:
            params.append(p(
                "vm.nr_hugepages", str(hp), MED,
                f"Static 2MB huge pages = {hp:,} = {inp.hugepage_size_gb}GB / 2MB. "
                "Static hugepages: pre-allocated at boot, never swapped, zero THP overhead. "
                "PostgreSQL: set shared_memory_type=mmap to use hugepages. "
                "JVM: use -XX:+UseHugeTLBFS or -XX:+UseLargePages. "
                "Verify: grep HugePages /proc/meminfo",
                f"vm.nr_hugepages = {hp}",
                ex.vm_nr_hugepages,
            ))

        params += [
            p(
                "kernel.randomize_va_space", "2", MIN,
                "ASLR full randomisation. "
                "Default 0 on some minimal installs = no ASLR. "
                "ASLR=2: randomise stack, VDSO, shared memory, heap. "
                "Prevents ROP (Return-Oriented Programming) exploits. "
                "CIS Benchmark: required.",
                "kernel.randomize_va_space = 2",
                ex.kernel_randomize_va_space,
                safe=False,
            ),
            p(
                "kernel.kptr_restrict", "2", MIN,
                "Hide kernel symbol addresses from /proc/kallsyms. "
                "Default 0: any process can read kernel addresses → "
                "enables kernel exploit address reuse. "
                "=2: hidden from all users including root.",
                "kernel.kptr_restrict = 2",
                ex.kernel_kptr_restrict,
                safe=False,
            ),
            p(
                "systemd DefaultLimitNOFILE", str(nf), MIN,
                f"systemd system.conf DefaultLimitNOFILE={nf}. "
                "Without this: systemd-managed services start with default 1024 FDs "
                "regardless of /etc/security/limits.conf. "
                "Affects: NGINX, PostgreSQL, Redis, Tomcat when started via systemd. "
                "Apply: systemctl daemon-reexec",
                f"[Manager]
DefaultLimitNOFILE={nf}",
                ex.systemd_default_limit_nofile,
                safe=False,
            ),
            p(
                "ip_local_port_range", "1024 65535", MIN,
                "Ephemeral port range = 1024–65535 (64511 ports). "
                "Default: 32768–60999 = 28232 ports. "
                "Reverse proxy / outbound-heavy: 28K ports exhausted at ~28K outbound connections. "
                "Extended range: 2.28× more outbound connections before TIME_WAIT exhaustion.",
                "net.ipv4.ip_local_port_range = 1024 65535",
                ex.net_ipv4_ip_local_port_range,
            ),
            p(
                "net.ipv4.tcp_syncookies", "1", MIN,
                "SYN cookies: when SYN backlog full, encode connection state in SYN-ACK. "
                "Protects against SYN flood attacks — new connections still accepted "
                "even when backlog is full. "
                "Always enabled in production.",
                "net.ipv4.tcp_syncookies = 1",
                ex.net_ipv4_tcp_syncookies,
                safe=False,
            ),
        ]

        return params

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        def _int(v):
            try: return int(v)
            except: return None

        if (v := _int(ex.net_core_somaxconn)) and v < 65535:
            findings.append(
                f"[MAJOR] net.core.somaxconn={v} — too low. "
                f"TCP accept queue exhausted at {v}+1 connections. Recommended: {self._somaxconn()}."
            )
        if (v := _int(ex.fs_file_max)) and v < 1_000_000:
            findings.append(
                f"[MAJOR] fs.file-max={v:,} — too low for production. "
                f"Recommended: {self._file_max():,}."
            )
        if (v := _int(ex.ulimit_nofile_soft)) and v <= 1024:
            findings.append(
                f"[MAJOR] ulimit nofile={v} — default Linux value. "
                "NGINX/Tomcat/Redis will fail at 1025th file descriptor. "
                f"Recommended: {self._nofile():,}."
            )
        if (v := _int(ex.vm_swappiness)) and v > 20 and self.inp.workload_role in ("database", "cache"):
            findings.append(
                f"[MAJOR] vm.swappiness={v} for {self.inp.workload_role}. "
                "Database/cache swap causes 1000× latency spikes. "
                f"Recommended: {self._swappiness()}."
            )
        if ex.kernel_randomize_va_space == "0":
            findings.append(
                "[MAJOR] kernel.randomize_va_space=0 — ASLR disabled. "
                "Critical security vulnerability. Set to 2 immediately."
            )
        if (v := _int(ex.kernel_pid_max)) and v <= 32768:
            findings.append(
                f"[MEDIUM] kernel.pid_max={v} — default. "
                "Exhausted by JVM thread pools or container workloads. "
                f"Recommended: {self._pid_max():,}."
            )
        if ex.net_ipv4_tcp_tw_reuse == "0":
            findings.append(
                "[MEDIUM] net.ipv4.tcp_tw_reuse=0. "
                "TIME_WAIT sockets not reused — ephemeral port exhaustion at high RPS. "
                "Set to 1."
            )
        if (v := _int(ex.net_ipv4_tcp_fin_timeout)) and v >= 60:
            findings.append(
                f"[MEDIUM] tcp_fin_timeout={v}s — default. "
                "Closed connections hold socket for {v}s. "
                "At 10K closes/sec: {v*10000} stale sockets. Reduce to 15s."
            )
        if ex.transparent_hugepage == "always" and self.inp.workload_role in ("database", "cache"):
            findings.append(
                "[MAJOR] transparent_hugepage=always for database/cache. "
                "THP compaction causes 10-100ms latency stalls. "
                "Set to 'never' for PostgreSQL/MySQL/Redis."
            )
        if ex.io_scheduler == "cfq":
            findings.append(
                "[MEDIUM] I/O scheduler=cfq (legacy). "
                "CFQ removed in kernel 5.0+. "
                f"Recommended: {self._io_scheduler()} for {self.inp.disk_type}."
            )
        if ex.vm_max_map_count and _int(ex.vm_max_map_count) and _int(ex.vm_max_map_count) < 262144:
            findings.append(
                f"[MEDIUM] vm.max_map_count={ex.vm_max_map_count} — too low for JVM/Elasticsearch. "
                "Set to 1048576."
            )

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> OSLinuxOutput:
        all_params = self._build_params()
        major, medium, minor = self._split(all_params)

        return OSLinuxOutput(
            mode                = self.inp.mode,
            somaxconn           = self._somaxconn(),
            tcp_max_syn_backlog = self._somaxconn(),
            rmem_max            = self._rmem_max(),
            wmem_max            = self._rmem_max(),
            file_max            = self._file_max(),
            nofile_soft         = self._nofile(),
            nofile_hard         = self._nofile(),
            nr_hugepages        = self._nr_hugepages(),
            pid_max             = self._pid_max(),
            sysctl_conf         = self._render_sysctl(),
            limits_conf         = self._render_limits_conf(),
            systemd_override    = self._render_systemd_override(),
            tuned_profile       = self._render_tuned_profile(),
            apply_script        = self._render_apply_script(),
            major_params        = major,
            medium_params       = medium,
            minor_params        = minor,
            ha_suggestions=[
                "Use Ansible / Puppet to apply this sysctl profile across all nodes consistently.",
                "Add sysctl settings to cloud-init user-data for auto-apply on VM provisioning.",
                "Persist I/O scheduler changes via udev rule: "
                "ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/scheduler}="mq-deadline"",
                "Monitor FD exhaustion: Prometheus node_exporter → "
                "node_filefd_allocated / node_filefd_maximum.",
                "NUMA: use numactl --membind + taskset to pin database processes to NUMA node.",
                "For containers: apply sysctl via DaemonSet (privileged) or node-level tuned profile.",
            ],
            performance_warnings=[w for w in [
                ("workload_role=database with enable_hugepages=False. "
                 "PostgreSQL/Oracle benefits significantly from huge pages. "
                 "Enable hugepage_size_gb ≥ shared_buffers size.")
                if self.inp.workload_role == "database" and not self.inp.enable_hugepages else None,
                (f"network_speed_gbps={self.inp.network_speed_gbps} but rmem_max={self._rmem_max():,}. "
                 "BDP at 100ms RTT requires larger buffers for full NIC utilisation.")
                if self.inp.network_speed_gbps >= 25 and self._rmem_max() < 134_217_728 else None,
                ("NUMA nodes > 1 detected. Ensure NUMA-aware memory allocation "
                 "in JVM (-XX:+UseNUMA) and database (numactl --interleave).")
                if self.inp.numa_nodes > 1 else None,
            ] if w],
            capacity_warning    = None,
            audit_findings      = self._audit()
                                  if self.inp.mode == CalcMode.EXISTING else [],
        )


