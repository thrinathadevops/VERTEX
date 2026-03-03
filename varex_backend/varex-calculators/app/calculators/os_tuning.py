"""
app/calculators/os_tuning.py
============================
Shared Linux kernel / OS tuning engine used by every VAREX component
calculator (NGINX, Redis, Tomcat, HTTPD, OHS, IHS, Podman, Kubernetes).

Generates 22+ sysctl / ulimit parameters with deep formula-based reasoning.
OS-specific extras (conntrack) are injected automatically based on os_type.

Usage
-----
    engine = OSTuningEngine(
        cpu=4, ram_gb=32, max_conns=10000,
        os_type=OSType.UBUNTU_22,
        existing={"vm.swappiness": "60"},   # from existing audit
        disable_thp=True,                    # True for Redis / JVM workloads
    )
    params     = engine.generate()           # list[TuningParam]
    sysctl_blk = engine.sysctl_block()       # ready-to-paste /etc/sysctl.d/ file
"""
from __future__ import annotations

from app.calculators.base import BaseCalculator
from app.core.enums import ImpactLevel, OSType

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class OSTuningEngine(BaseCalculator):
    """
    Parameters
    ----------
    cpu         : number of vCPUs / physical cores
    ram_gb      : total RAM in GB
    max_conns   : peak simultaneous connections the service will handle
                  (e.g. worker_connections×workers for NGINX,
                   maxThreads for Tomcat, maxmemory_clients for Redis)
    os_type     : OSType enum — drives OS-specific sysctl extras
    existing    : dict of current sysctl values from audit  {key: str_value}
    disable_thp : True → add transparent_hugepage=never param
                  (mandatory for Redis, JVM/Tomcat, anything that fork()s)
    """

    def __init__(
        self,
        cpu:         int,
        ram_gb:      float,
        max_conns:   int,
        os_type:     OSType,
        existing:    dict[str, str] | None = None,
        disable_thp: bool = False,
    ) -> None:
        self.cpu         = cpu
        self.ram_gb      = ram_gb
        self.max_conns   = max_conns
        self.os_type     = os_type
        self.existing    = existing or {}
        self.disable_thp = disable_thp

    # ── internal helpers ──────────────────────────────────────────────────────
    def _c(self, key: str) -> str | None:
        """Lookup current sysctl value from the existing audit dict."""
        return self.existing.get(key)

    def _fd(self) -> int:
        """
        Per-process file-descriptor limit.
        Formula: max(max_conns × 2, 65535)
        ×2 because each proxied connection uses 2 FDs: client socket + upstream socket.
        Floor of 65535 ensures a sane minimum even for low-traffic services.
        """
        return max(self.max_conns * 2, 65_535)

    def _rmem(self) -> int:
        """
        Max TCP socket buffer size.
        Formula: min(5% of RAM in bytes, 256MB hard cap)
        5% of RAM avoids over-allocating buffers on RAM-constrained nodes.
        256MB cap prevents kernel OOM from runaway socket buffers.
        BDP (Bandwidth-Delay Product) rationale: at 10Gbps × 1ms RTT = 1.25MB optimal buffer.
        5% of 32GB = 1.6GB → capped at 256MB, which covers 10Gbps × 200ms RTT links.
        """
        return min(int(self.ram_gb * 1024 * 1024 * 1024 * 0.05), 268_435_456)

    def _sc(self) -> int:
        """
        Accept-queue depth.
        Formula: max(max_conns, 65535)
        Must be >= the service's worker thread / connection count.
        """
        return max(self.max_conns, 65_535)

    # ── main parameter generator ──────────────────────────────────────────────
    def generate(self) -> list:
        """
        Return a list[TuningParam] covering all OS-level tuning.
        Params are ordered by impact (MAJOR → MEDIUM → MINOR).
        OS-specific params appended at end.
        """
        p   = self._p
        fd  = self._fd()
        rm  = self._rmem()
        sc  = self._sc()
        cpu = self.cpu

        params = []

        # ── OPTIONAL: Transparent HugePages (THP) ────────────────────────────
        if self.disable_thp:
            params.append(p(
                "transparent_hugepage", "never", M,
                "THP causes 2–10 second latency spikes during copy-on-write fork operations. "
                "When Redis executes BGSAVE / BGREWRITEAOF, the kernel forks the process. "
                "During fork, THP splits huge pages back into base 4KB pages — a blocking "
                "operation that stops the Redis event loop for seconds. Same issue occurs "
                "during JVM GC (ParallelGC, G1GC). MANDATORY disable for Redis, "
                "Tomcat/JVM, and any service that uses fork(). "
                "Set in /etc/rc.local or via a systemd unit to survive reboots.",
                "# Apply immediately:
"
                "echo never > /sys/kernel/mm/transparent_hugepage/enabled
"
                "echo never > /sys/kernel/mm/transparent_hugepage/defrag

"
                "# Persist across reboots — add to /etc/rc.local:
"
                "echo 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' >> /etc/rc.local
"
                "echo 'echo never > /sys/kernel/mm/transparent_hugepage/defrag'  >> /etc/rc.local
"
                "chmod +x /etc/rc.local",
                self._c("transparent_hugepage"),
                safe=False,
            ))

        # ── MAJOR: stability / capacity ───────────────────────────────────────
        params += [
            p(
                "fs.file-max", str(fd * cpu), M,
                f"Global OS file-descriptor ceiling = max_conns×2×cpu_cores = {fd}×{cpu} = {fd*cpu}. "
                "This is the kernel-wide FD ceiling for ALL processes on the host. "
                "Breaching it causes 'Too many open files' errors at the OS level, "
                "crashing every process trying to open a socket, file, or pipe. "
                "Formula justification: each connection needs 2 FDs (client socket + upstream socket), "
                "multiplied by CPU count to account for parallel workers.",
                f"sysctl -w fs.file-max={fd * cpu}
"
                f"# Persist:
echo 'fs.file-max = {fd * cpu}' >> /etc/sysctl.d/99-varex.conf
"
                f"sysctl -p /etc/sysctl.d/99-varex.conf",
                self._c("fs.file-max"),
            ),
            p(
                "net.core.somaxconn", str(sc), M,
                f"TCP accept-queue depth = {sc}. "
                "The Linux default is 128 — the kernel silently drops SYN packets when the "
                "accept queue is full. With default 128: at 1000 concurrent clients arriving "
                "in a burst, 872 connections are silently refused. "
                "Must be ≥ max(worker_connections, maxThreads, MaxRequestWorkers) for the "
                "service running on this host. "
                "Note: nginx/Apache/Tomcat use backlog= in their config — this OS value "
                "is the hard ceiling they cannot exceed.",
                f"sysctl -w net.core.somaxconn={sc}
"
                f"echo 'net.core.somaxconn = {sc}' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.core.somaxconn"),
            ),
            p(
                "net.ipv4.tcp_max_syn_backlog", str(sc), M,
                f"SYN backlog queue per listening socket = {sc}. "
                "This is a separate queue from somaxconn — the lower of the two silently "
                "caps the effective accept queue, causing SYN drops without any log entry. "
                "Both must be set to the same value.",
                f"sysctl -w net.ipv4.tcp_max_syn_backlog={sc}
"
                f"echo 'net.ipv4.tcp_max_syn_backlog = {sc}' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_max_syn_backlog"),
            ),
            p(
                "vm.overcommit_memory", "1", M,
                "Default=0: kernel checks each malloc() against current free RAM. "
                "When RSS > free_RAM, fork() returns ENOMEM — even when 40% RAM is free — "
                "because the kernel pessimistically assumes the child will dirty all pages. "
                "Redis BGSAVE and BGREWRITEAOF rely on fork(). With overcommit=0: "
                "Redis logs 'Can\'t save in background: fork: Cannot allocate memory' "
                "and persistence silently stops. JVM subprocess creation also fails. "
                "Setting to 1 (always allow overcommit) is safe because Linux uses "
                "copy-on-write — child processes only consume RAM for pages they actually modify.",
                "sysctl -w vm.overcommit_memory=1
"
                "echo 'vm.overcommit_memory = 1' >> /etc/sysctl.d/99-varex.conf",
                self._c("vm.overcommit_memory"),
            ),
            p(
                "ulimit -n  (nofile)", str(fd), M,
                f"Per-process file-descriptor limit = {fd}. "
                f"Formula: max_conns×2 = {self.max_conns}×2 = {fd}. "
                "FD consumption breakdown by service:
"
                "  NGINX:      worker_connections × 2 (client + upstream FDs)
"
                "  Redis:      1 FD per client + 32 internal (AOF, RDB, cluster)
"
                "  Tomcat:     maxThreads × 4 (socket + log + class files)
"
                "  HTTPD/IHS:  MaxRequestWorkers × 3
"
                "Must be persisted in both /etc/security/limits.conf AND "
                "the systemd service unit (LimitNOFILE=) — systemd overrides "
                "limits.conf for services started via systemctl.",
                f"ulimit -n {fd}

"
                f"# Persist for ALL users:
"
                f"echo '* soft nofile {fd}' >> /etc/security/limits.conf
"
                f"echo '* hard nofile {fd}' >> /etc/security/limits.conf

"
                f"# Persist for systemd-managed services (REQUIRED for nginx/redis/tomcat units):
"
                f"# Add to [Service] section of /etc/systemd/system/<service>.service:
"
                f"# LimitNOFILE={fd}
"
                f"systemctl daemon-reload && systemctl restart <service>",
                self._c("ulimit_nofile"),
            ),
        ]

        # ── MEDIUM: performance / network ─────────────────────────────────────
        params += [
            p(
                "net.core.rmem_max", str(rm), MED,
                f"Max TCP receive buffer = {rm:,} bytes (5% of {self.ram_gb}GB RAM). "
                "BDP formula: optimal_buffer = bandwidth × RTT. "
                "At 10Gbps × 1ms RTT = 1.25MB; at 1Gbps × 10ms RTT = 1.25MB. "
                "Larger buffers reduce retransmissions and improve throughput on high-bandwidth links. "
                "The kernel auto-tunes per-socket buffers up to this max.",
                f"sysctl -w net.core.rmem_max={rm}
"
                f"echo 'net.core.rmem_max = {rm}' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.core.rmem_max"),
            ),
            p(
                "net.core.wmem_max", str(rm), MED,
                "Max TCP send buffer — mirror of rmem_max. Set equal for symmetric throughput.",
                f"sysctl -w net.core.wmem_max={rm}
"
                f"echo 'net.core.wmem_max = {rm}' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.core.wmem_max"),
            ),
            p(
                "net.ipv4.tcp_rmem", f"4096 87380 {rm}", MED,
                "Per-socket receive buffer: min / default / max. "
                "Kernel auto-tunes between min and max based on available memory. "
                "Default max = 212992 (208KB) — insufficient for GbE transfers. "
                f"Setting max to {rm:,} bytes matches rmem_max.",
                f"sysctl -w net.ipv4.tcp_rmem='4096 87380 {rm}'
"
                f"echo "net.ipv4.tcp_rmem = 4096 87380 {rm}" >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_rmem"),
            ),
            p(
                "net.ipv4.tcp_wmem", f"4096 65536 {rm}", MED,
                f"Per-socket send buffer: min / default / max = {rm:,} bytes.",
                f"sysctl -w net.ipv4.tcp_wmem='4096 65536 {rm}'
"
                f"echo "net.ipv4.tcp_wmem = 4096 65536 {rm}" >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_wmem"),
            ),
            p(
                "net.ipv4.tcp_tw_reuse", "1", MED,
                "Reuse TIME_WAIT sockets for new outbound connections. "
                "Without this, each upstream connection holds an ephemeral port for 60 seconds. "
                "Math: 30,000 RPS × 60s TIME_WAIT = 1,800,000 ports needed. "
                "Default ephemeral range = 32768–60999 = only 28,231 ports. "
                "Result at 30K RPS: 'Cannot assign requested address' within 1 second. "
                "tcp_tw_reuse solves this by safely recycling TIME_WAIT sockets "
                "when a new SYN arrives with a higher timestamp (RFC 6191).",
                "sysctl -w net.ipv4.tcp_tw_reuse=1
"
                "echo 'net.ipv4.tcp_tw_reuse = 1' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_tw_reuse"),
            ),
            p(
                "net.ipv4.tcp_fin_timeout", "15", MED,
                "Reduce TIME_WAIT socket lifetime from 60s to 15s. "
                "Sockets in TIME_WAIT consume: 1 FD, ~300 bytes kernel memory, 1 ephemeral port. "
                "Reducing from 60s to 15s reclaims resources 4× faster. "
                "Safe for server-side sockets because the kernel still enforces TCP sequence checks.",
                "sysctl -w net.ipv4.tcp_fin_timeout=15
"
                "echo 'net.ipv4.tcp_fin_timeout = 15' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_fin_timeout"),
            ),
            p(
                "net.ipv4.ip_local_port_range", "1024 65535", MED,
                "Widen ephemeral outbound port range from default 32768–60999 (~28K ports) "
                "to 1024–65535 (~64K ports). "
                "Critical for reverse-proxy servers (NGINX, HTTPD, IHS, OHS) that open "
                "thousands of outbound connections to upstream backends. "
                "Ports < 1024 are privileged; starting from 1024 is safe.",
                "sysctl -w net.ipv4.ip_local_port_range='1024 65535'
"
                "echo 'net.ipv4.ip_local_port_range = 1024 65535' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.ip_local_port_range"),
            ),
            p(
                "net.core.netdev_max_backlog", "250000", MED,
                "NIC receive queue length before the kernel starts dropping packets. "
                "Default = 1000. A 10GbE NIC at line rate delivers ~14.8 million 64-byte "
                "packets/sec — far exceeding the default queue. "
                "Setting to 250,000 provides headroom for micro-bursts.",
                "sysctl -w net.core.netdev_max_backlog=250000
"
                "echo 'net.core.netdev_max_backlog = 250000' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.core.netdev_max_backlog"),
            ),
            p(
                "vm.swappiness", "10", MED,
                "Controls kernel willingness to swap application pages to disk. "
                "Default = 60: kernel starts swapping hot pages when RAM is 40% free, "
                "causing 10–100ms latency spikes when swapped pages are faulted back. "
                "Value 10: only swap when RAM < 10% free, keeping working set in RAM. "
                "Set to 1 for Redis-only nodes (near-zero swap). "
                "Never set to 0 — that risks OOM killer activation under pressure.",
                "sysctl -w vm.swappiness=10
"
                "echo 'vm.swappiness = 10' >> /etc/sysctl.d/99-varex.conf",
                self._c("vm.swappiness"),
            ),
            p(
                "net.ipv4.tcp_slow_start_after_idle", "0", MED,
                "Prevents TCP slow-start on keep-alive connections that have been idle. "
                "Default = 1: after idle, kernel resets congestion window (cwnd) to initial "
                "value (~10 MSS), halving throughput for the first request after any pause. "
                "For APIs with bursty traffic (cron jobs, health checks, batch requests), "
                "this causes consistent throughput degradation on the first request of each burst.",
                "sysctl -w net.ipv4.tcp_slow_start_after_idle=0
"
                "echo 'net.ipv4.tcp_slow_start_after_idle = 0' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_slow_start_after_idle"),
            ),
            p(
                "vm.dirty_ratio", "15", MED,
                "Maximum % of RAM that can hold dirty (unwritten to disk) pages before "
                "application processes are blocked waiting for writeback to complete. "
                "Default = 20%: on a 32GB server, 6.4GB of dirty pages accumulate before "
                "any process is blocked — causing a sudden 1–5 second write stall when the "
                "threshold is hit. Setting to 15% triggers writeback earlier, smoothing I/O.",
                "sysctl -w vm.dirty_ratio=15
"
                "echo 'vm.dirty_ratio = 15' >> /etc/sysctl.d/99-varex.conf",
                self._c("vm.dirty_ratio"),
            ),
            p(
                "vm.dirty_background_ratio", "5", MED,
                "% of RAM at which background kernel writeback (pdflush/kworker) starts. "
                "Default = 10%: background writeback starts late, allowing large dirty page "
                "accumulation and erratic I/O patterns. "
                "Setting to 5% keeps dirty pages continuously flushed.",
                "sysctl -w vm.dirty_background_ratio=5
"
                "echo 'vm.dirty_background_ratio = 5' >> /etc/sysctl.d/99-varex.conf",
                self._c("vm.dirty_background_ratio"),
            ),
        ]

        # ── MINOR: observability / fine-tuning ───────────────────────────────
        params += [
            p(
                "net.ipv4.tcp_keepalive_time", "300", MIN,
                "Start sending TCP keepalive probes after 300s of idle connection. "
                "Default = 7200s (2 hours). A dead upstream connection discovered after "
                "2 hours blocks a worker thread for 2 hours. "
                "300s = 5 minutes idle detection.",
                "sysctl -w net.ipv4.tcp_keepalive_time=300
"
                "echo 'net.ipv4.tcp_keepalive_time = 300' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_keepalive_time"),
            ),
            p(
                "net.ipv4.tcp_keepalive_intvl", "30", MIN,
                "Interval between keepalive probes = 30s (default 75s). "
                "Total detection time = keepalive_time + probes×intvl = 300 + 5×30 = 450s.",
                "sysctl -w net.ipv4.tcp_keepalive_intvl=30
"
                "echo 'net.ipv4.tcp_keepalive_intvl = 30' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_keepalive_intvl"),
            ),
            p(
                "net.ipv4.tcp_keepalive_probes", "5", MIN,
                "Declare connection dead after 5 failed keepalive probes. "
                "Total detection time = 300 + 5×30 = 450 seconds.",
                "sysctl -w net.ipv4.tcp_keepalive_probes=5
"
                "echo 'net.ipv4.tcp_keepalive_probes = 5' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_keepalive_probes"),
            ),
            p(
                "kernel.pid_max", "65536", MIN,
                "Default = 32768. Exhausted by: JVM with 500+ threads (each thread = 1 PID), "
                "Kubernetes with many containers, Podman rootless with multiple pods. "
                "Symptom: 'fork: resource temporarily unavailable' with no clear cause.",
                "sysctl -w kernel.pid_max=65536
"
                "echo 'kernel.pid_max = 65536' >> /etc/sysctl.d/99-varex.conf",
                self._c("kernel.pid_max"),
            ),
            p(
                "net.ipv4.tcp_congestion_control", "bbr", MIN,
                "BBR (Bottleneck Bandwidth and RTT, Google 2016) replaces CUBIC. "
                "CUBIC is loss-based: it only backs off after packet loss, by which time "
                "buffers are already full (bufferbloat). "
                "BBR is model-based: it continuously measures bandwidth and RTT to maintain "
                "optimal sending rate. Result: higher throughput + lower latency, especially "
                "effective in cloud environments with variable RTT and behind load balancers. "
                "Requires kernel 4.9+.",
                "modprobe tcp_bbr
"
                "sysctl -w net.ipv4.tcp_congestion_control=bbr
"
                "echo 'net.ipv4.tcp_congestion_control = bbr' >> /etc/sysctl.d/99-varex.conf
"
                "# Verify: sysctl net.ipv4.tcp_congestion_control",
                self._c("net.ipv4.tcp_congestion_control"),
            ),
            p(
                "net.core.optmem_max", "81920", MIN,
                "Max size of per-socket option memory buffer. "
                "Default 20KB. Required for AF_PACKET sockets and advanced socket options "
                "used by Kubernetes CNI plugins (Calico, Cilium).",
                "sysctl -w net.core.optmem_max=81920
"
                "echo 'net.core.optmem_max = 81920' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.core.optmem_max"),
            ),
        ]

        # ── OS-specific: conntrack ────────────────────────────────────────────
        if self.os_type in (OSType.RHEL_8, OSType.RHEL_9):
            params.append(p(
                "nf_conntrack_max", "1048576", MED,
                "RHEL 8/9 default nf_conntrack table is typically 65536. "
                "At >100K concurrent connections, the table overflows and the kernel "
                "silently drops NEW connection packets with no log entry. "
                "Symptom: intermittent connection timeouts with no application-level errors. "
                "1048576 = 1M entries handles large-scale microservice mesh traffic.",
                "sysctl -w net.netfilter.nf_conntrack_max=1048576
"
                "echo 'net.netfilter.nf_conntrack_max = 1048576' >> /etc/sysctl.d/99-varex.conf
"
                "# Also increase conntrack buckets:
"
                "echo 262144 > /sys/module/nf_conntrack/parameters/hashsize",
                self._c("net.netfilter.nf_conntrack_max"),
            ))

        if self.os_type == OSType.CENTOS_7:
            params.append(p(
                "nf_conntrack_max", "524288", MED,
                "CentOS 7 default conntrack table (~65K) fills rapidly under microservice "
                "mesh traffic or when running as a reverse proxy with many upstream connections. "
                "524288 = 512K entries provides safe headroom.",
                "sysctl -w net.netfilter.nf_conntrack_max=524288
"
                "echo 'net.netfilter.nf_conntrack_max = 524288' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.netfilter.nf_conntrack_max"),
            ))

        if self.os_type in (OSType.AMAZON_2, OSType.AMAZON_2023):
            params.append(p(
                "net.ipv4.tcp_mtu_probing", "1", MIN,
                "Amazon Linux: enable MTU path discovery to handle jumbo frames on VPC. "
                "Without this, PMTUD blackholes cause silent packet drops on some EC2 instance types.",
                "sysctl -w net.ipv4.tcp_mtu_probing=1
"
                "echo 'net.ipv4.tcp_mtu_probing = 1' >> /etc/sysctl.d/99-varex.conf",
                self._c("net.ipv4.tcp_mtu_probing"),
            ))

        return params

    # ── sysctl file generator ─────────────────────────────────────────────────
    def sysctl_block(self) -> str:
        """
        Render all sysctl params as a ready-to-paste
        /etc/sysctl.d/99-varex.conf file block.

        Excludes ulimit, transparent_hugepage, and kernel.pid_max
        (those need separate handling — limits.conf / rc.local).
        """
        EXCLUDE_PREFIXES = ("ulimit", "transparent", "kernel.pid")

        lines = [
            "# ╔══════════════════════════════════════════════════════════════╗",
            "# ║  VAREX OS Tuning                                             ║",
            "# ║  File:  /etc/sysctl.d/99-varex.conf                         ║",
            "# ║  Apply: sysctl -p /etc/sysctl.d/99-varex.conf               ║",
            "# ╚══════════════════════════════════════════════════════════════╝",
            "",
            "# ── MAJOR  (stability / capacity) ─────────────────────────────",
        ]

        current_tier = "MAJOR"
        for param in self.generate():
            # Skip params that don't map cleanly to sysctl key=value
            if any(param.name.startswith(x) for x in EXCLUDE_PREFIXES):
                continue
            if "." not in param.name:
                continue

            tier = param.impact.value
            if tier != current_tier:
                current_tier = tier
                lines.append("")
                lines.append(f"# ── {tier}  {'(performance / network)' if tier == 'MEDIUM' else '(fine-tuning / observability)'} ──")

            current = f"  # was: {param.current_value}" if param.current_value else ""
            lines.append(f"{param.name} = {param.recommended}   # [{tier}]{current}")

        lines += [
            "",
            "# ── ulimit: set in /etc/security/limits.conf  ─────────────────",
            f"# * soft nofile {self._fd()}",
            f"# * hard nofile {self._fd()}",
            "",
            "# ── systemd service unit (LimitNOFILE overrides limits.conf) ──",
            f"# LimitNOFILE={self._fd()}",
        ]

        if self.disable_thp:
            lines += [
                "",
                "# ── THP: set in /etc/rc.local (not sysctl) ─────────────────",
                "# echo never > /sys/kernel/mm/transparent_hugepage/enabled",
                "# echo never > /sys/kernel/mm/transparent_hugepage/defrag",
            ]

        return "
".join(lines)
