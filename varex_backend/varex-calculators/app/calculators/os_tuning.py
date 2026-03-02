"""
Shared OS / kernel tuning parameter generator.
Covers: file descriptors, TCP stack, VM, huge-pages.
Parameters are tagged MAJOR / MEDIUM / MINOR by production impact.
"""
from __future__ import annotations
from app.core.enums import ImpactLevel, OSType
from app.core.models import TuningParam
from app.calculators.base import BaseCalculator


class OSTuningEngine(BaseCalculator):
    """
    Generates kernel sysctl recommendations based on workload profile.

    Parameters
    ----------
    cpu_cores    : int   – detected / declared CPU count
    ram_gb       : float – total RAM in GB
    max_conns    : int   – peak simultaneous connections expected
    os_type      : OSType
    existing_params : dict[str, str] | None
        If provided (EXISTING mode) maps sysctl key → current string value.
    disable_thp  : bool  – True for Redis workloads
    """

    def __init__(
        self,
        cpu_cores: int,
        ram_gb: float,
        max_conns: int,
        os_type: OSType,
        existing_params: dict[str, str] | None = None,
        disable_thp: bool = False,
    ) -> None:
        self._require_positive(cpu_cores, "cpu_cores")
        self._require_positive(ram_gb,    "ram_gb")
        self._require_positive(max_conns, "max_conns")
        self.cpu_cores  = cpu_cores
        self.ram_gb     = ram_gb
        self.max_conns  = max_conns
        self.os_type    = os_type
        self.existing   = existing_params or {}
        self.disable_thp = disable_thp

    # ── helpers ───────────────────────────────────────────────────────────
    def _cur(self, key: str) -> str | None:
        return self.existing.get(key)

    def _rmem(self) -> int:
        # 256 KB per connection, capped at 256 MB
        return min(int(self.ram_gb * 1024 * 1024 * 1024 * 0.05), 268_435_456)

    def _somaxconn(self) -> int:
        return max(self.max_conns, 65_535)

    def generate(self) -> list[TuningParam]:
        p = self._param
        M, MED, MIN = ImpactLevel.MAJOR, ImpactLevel.MEDIUM, ImpactLevel.MINOR
        fd_limit = max(self.max_conns * 2, 65_535)
        rmem = self._rmem()
        smaxconn = self._somaxconn()

        params: list[TuningParam] = [
            # ── MAJOR ────────────────────────────────────────────────────
            p("fs.file-max",
              str(fd_limit * self.cpu_cores),
              M,
              "Sets the global OS file-descriptor ceiling. "
              "Too low → 'Too many open files' crashes under load.",
              f"sysctl -w fs.file-max={fd_limit * self.cpu_cores}",
              self._cur("fs.file-max")),

            p("net.core.somaxconn",
              str(smaxconn),
              M,
              "Max length of the accept queue. Values below concurrent connections "
              "cause silent TCP SYN drops under burst traffic.",
              f"sysctl -w net.core.somaxconn={smaxconn}",
              self._cur("net.core.somaxconn")),

            p("net.ipv4.tcp_max_syn_backlog",
              str(smaxconn),
              M,
              "SYN backlog queue. Must match somaxconn to prevent SYN floods "
              "from dropping legitimate connections.",
              f"sysctl -w net.ipv4.tcp_max_syn_backlog={smaxconn}",
              self._cur("net.ipv4.tcp_max_syn_backlog")),

            p("vm.overcommit_memory",
              "1",
              M,
              "Required for Redis fork-based persistence. Default=0 can cause "
              "ENOMEM on fork() even when physical RAM is available.",
              "sysctl -w vm.overcommit_memory=1",
              self._cur("vm.overcommit_memory")),

            p("ulimit -n (nofile)",
              str(fd_limit),
              M,
              "Per-process file-descriptor limit. Must cover worker_connections×2 "
              "for NGINX, and all Redis/Tomcat socket handles.",
              f"ulimit -n {fd_limit}  # add to /etc/security/limits.conf for persistence",
              self._cur("ulimit_nofile")),

            # ── MEDIUM ───────────────────────────────────────────────────
            p("net.core.rmem_max",
              str(rmem),
              MED,
              "Max receive socket buffer. Larger buffers reduce retransmissions "
              "on high-throughput or high-latency paths.",
              f"sysctl -w net.core.rmem_max={rmem}",
              self._cur("net.core.rmem_max")),

            p("net.core.wmem_max",
              str(rmem),
              MED,
              "Max send socket buffer. Mirrors rmem_max for balanced throughput.",
              f"sysctl -w net.core.wmem_max={rmem}",
              self._cur("net.core.wmem_max")),

            p("net.ipv4.tcp_tw_reuse",
              "1",
              MED,
              "Reuse TIME_WAIT sockets for new outbound connections. "
              "Prevents port exhaustion on high-RPS APIs.",
              "sysctl -w net.ipv4.tcp_tw_reuse=1",
              self._cur("net.ipv4.tcp_tw_reuse")),

            p("net.ipv4.tcp_fin_timeout",
              "15",
              MED,
              "Reduce TIME_WAIT lifetime from 60s default. "
              "Frees port/socket resources faster after connections close.",
              "sysctl -w net.ipv4.tcp_fin_timeout=15",
              self._cur("net.ipv4.tcp_fin_timeout")),

            p("net.ipv4.ip_local_port_range",
              "1024 65535",
              MED,
              "Widens the ephemeral port range from the default 32768-60999, "
              "preventing port exhaustion on outbound proxy connections.",
              "sysctl -w net.ipv4.ip_local_port_range='1024 65535'",
              self._cur("net.ipv4.ip_local_port_range")),

            p("net.core.netdev_max_backlog",
              "250000",
              MED,
              "NIC receive queue length. Prevents packet drops on NICs that "
              "deliver bursts faster than the kernel can process them.",
              "sysctl -w net.core.netdev_max_backlog=250000",
              self._cur("net.core.netdev_max_backlog")),

            p("vm.swappiness",
              "10",
              MED,
              "Reduce kernel tendency to swap. High swappiness evicts hot "
              "memory pages causing latency spikes on memory-intensive apps.",
              "sysctl -w vm.swappiness=10",
              self._cur("vm.swappiness")),

            # ── MINOR ────────────────────────────────────────────────────
            p("net.ipv4.tcp_keepalive_time",
              "300",
              MIN,
              "Start keepalive probes after 300s idle. Helps detect dead "
              "connections to upstreams without waiting the full TCP timeout.",
              "sysctl -w net.ipv4.tcp_keepalive_time=300",
              self._cur("net.ipv4.tcp_keepalive_time")),

            p("net.ipv4.tcp_keepalive_intvl",
              "30",
              MIN,
              "Interval between keepalive probes.",
              "sysctl -w net.ipv4.tcp_keepalive_intvl=30",
              self._cur("net.ipv4.tcp_keepalive_intvl")),

            p("net.ipv4.tcp_keepalive_probes",
              "5",
              MIN,
              "Number of failed probes before declaring the connection dead.",
              "sysctl -w net.ipv4.tcp_keepalive_probes=5",
              self._cur("net.ipv4.tcp_keepalive_probes")),

            p("kernel.pid_max",
              "65536",
              MIN,
              "Max PID number. Low values prevent forking under high-concurrency "
              "Tomcat or Python gunicorn deployments.",
              "sysctl -w kernel.pid_max=65536",
              self._cur("kernel.pid_max")),
        ]

        if self.disable_thp:
            params.insert(0, p(
                "transparent_hugepage",
                "never",
                M,
                "THP causes severe latency spikes during Redis fork-based "
                "persistence (BGSAVE/BGREWRITEAOF). Must be disabled for Redis.",
                "echo never > /sys/kernel/mm/transparent_hugepage/enabled  "
                "# persist via rc.local or systemd unit",
                self._cur("transparent_hugepage"),
            ))

        # OS-specific notes
        if self.os_type in (OSType.RHEL_8, OSType.RHEL_9):
            params.append(p(
                "selinux_mode (RHEL)",
                "enforcing",
                MIN,
                "Keep SELinux enforcing; label NGINX/Tomcat dirs with "
                "httpd_sys_content_t rather than disabling.",
                "# semanage fcontext -a -t httpd_sys_content_t '/srv/www(/.*)?'",
                self._cur("selinux"),
            ))
        if self.os_type == OSType.CENTOS_7:
            params.append(p(
                "nf_conntrack_max (CentOS 7)",
                "524288",
                MED,
                "CentOS 7 default conntrack table is too small for high-RPS "
                "workloads; fills up causing packet drops.",
                "sysctl -w net.netfilter.nf_conntrack_max=524288",
                self._cur("net.netfilter.nf_conntrack_max"),
            ))

        return params

    def sysctl_conf_block(self) -> str:
        """Returns a ready-to-paste /etc/sysctl.d/99-varex.conf block."""
        params = self.generate()
        lines = ["# /etc/sysctl.d/99-varex.conf – generated by VAREX Calculator",
                 "# Apply with: sysctl -p /etc/sysctl.d/99-varex.conf", ""]
        for p in params:
            if p.name.startswith("ulimit") or p.name.startswith("transparent"):
                lines.append(f"# {p.name} = {p.recommended}  # set separately (see command)")
            elif "." in p.name and not p.name.startswith("#"):
                lines.append(f"{p.name} = {p.recommended}   # [{p.impact.value}] {p.reason[:60]}")
        return "\n".join(lines)
