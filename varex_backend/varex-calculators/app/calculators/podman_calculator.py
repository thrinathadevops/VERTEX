"""
app/calculators/podman_calculator.py
=====================================
Podman container tuning calculator — NEW and EXISTING modes.

Resource limit formulas
-----------------------
CPU quota (cgroup cpu.max):
  cpu_quota  = int(container_cpu_cores × cpu_period)
  cpu_period = 100000 microseconds (100ms — Linux default)
  e.g.: 2 CPUs → quota=200000/period=100000 = 2 full CPUs

Memory limit:
  memory_limit_mb    = int(container_ram_gb × 1024)
  memory_swap_mb     = memory_limit_mb × 2
    (swap = RAM + swap space; × 2 allows 1× swap headroom)
    For database containers: set = memory_limit_mb (disable swap — latency)
  memory_reservation = memory_limit_mb × 0.80
    (soft limit — container can use more until host pressure)

PIDs limit:
  pids_limit = max(expected_pids × 2, 512)
  Prevents fork bombs. Default -1 = unlimited (dangerous in multi-tenant).

nofile ulimit:
  web/worker/batch  → 65535:65535
  database/cache    → 1048576:1048576  (high FD count for connections)

/dev/shm (shared memory):
  database containers: shm_size_mb = container_ram_gb × 1024 × 0.25
    (PostgreSQL uses shared_buffers in /dev/shm)
  others: user-supplied shm_size_mb
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.podman import PodmanInput, PodmanOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR

_CPU_PERIOD = 100_000   # 100ms Linux default cgroup period


class PodmanCalculator(BaseCalculator):

    def __init__(self, inp: PodmanInput) -> None:
        self._require_positive(inp.host_cpu_cores,      "host_cpu_cores")
        self._require_positive(inp.host_ram_gb,         "host_ram_gb")
        self._require_positive(inp.container_cpu_cores, "container_cpu_cores")
        self._require_positive(inp.container_ram_gb,    "container_ram_gb")
        if inp.container_cpu_cores > inp.host_cpu_cores:
            raise ValueError(
                f"container_cpu_cores ({inp.container_cpu_cores}) > "
                f"host_cpu_cores ({inp.host_cpu_cores})"
            )
        if inp.container_ram_gb > inp.host_ram_gb:
            raise ValueError(
                f"container_ram_gb ({inp.container_ram_gb}) > "
                f"host_ram_gb ({inp.host_ram_gb})"
            )
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _cpu_quota(self) -> int:
        return int(self.inp.container_cpu_cores * _CPU_PERIOD)

    def _mem_mb(self) -> int:
        return int(self.inp.container_ram_gb * 1024)

    def _mem_swap_mb(self) -> int:
        """Database: no swap (latency). Others: 2× RAM."""
        if self.inp.container_type in ("database", "cache"):
            return self._mem_mb()   # swap = RAM → effectively 0 extra swap
        return self._mem_mb() * 2

    def _mem_reservation_mb(self) -> int:
        return int(self._mem_mb() * 0.80)

    def _pids_limit(self) -> int:
        return max(self.inp.expected_pids * 2, 512)

    def _nofile(self) -> tuple[int, int]:
        if self.inp.container_type in ("database", "cache"):
            return (1_048_576, 1_048_576)
        return (65_535, 65_535)

    def _shm_mb(self) -> int:
        if self.inp.container_type in ("database", "cache"):
            return max(64, int(self.inp.container_ram_gb * 1024 * 0.25))
        return self.inp.shm_size_mb

    def _oom_score(self) -> int:
        """
        OOM score adjustment:
          batch     → +500  (kill first under memory pressure)
          database  → -500  (protect, kill last)
          cache     → -300
          web/worker→   0   (default, killed proportionally)
        """
        return {
            "batch":    500,
            "database": -500,
            "cache":    -300,
            "web":      0,
            "worker":   0,
        }.get(self.inp.container_type, 0)

    # ── security options ──────────────────────────────────────────────────────

    def _security_opts(self) -> list[str]:
        opts = []
        if self.inp.drop_all_caps:
            opts += [
                "--cap-drop=ALL",
                "--cap-add=NET_BIND_SERVICE",   # bind port < 1024
            ]
            if self.inp.container_type == "database":
                opts += ["--cap-add=IPC_LOCK"]  # mlock for database buffers
        if self.inp.read_only_rootfs:
            opts.append("--read-only")
        opts += [
            "--security-opt=no-new-privileges",
            "--security-opt=seccomp=unconfined",   # adjust to custom seccomp in prod
        ]
        if self.inp.rootless:
            opts.append("--userns=keep-id")
        return opts

    # ── podman run renderer ───────────────────────────────────────────────────

    def _render_run_flags(self) -> str:
        inp      = self.inp
        quota    = self._cpu_quota()
        mem      = self._mem_mb()
        swap     = self._mem_swap_mb()
        res      = self._mem_reservation_mb()
        pids     = self._pids_limit()
        nofile   = self._nofile()
        shm      = self._shm_mb()
        oom      = self._oom_score()
        sec_opts = self._security_opts()
        net_flag = f"--network={inp.network_mode}"

        sec_lines = "
".join(f"  {o} \" for o in sec_opts)

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Podman run flags  [{inp.mode.value.upper():8s}]  "
            f"type={inp.container_type}  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"podman run \
"
            f"  # ── CPU ──────────────────────────────────────────────────────
"
            f"  --cpus={inp.container_cpu_cores} \
"
            f"  --cpu-shares=1024 \
"
            f"  # ── Memory ───────────────────────────────────────────────────
"
            f"  --memory={mem}m \
"
            f"  --memory-swap={swap}m \
"
            f"  --memory-reservation={res}m \
"
            f"  # ── PIDs ─────────────────────────────────────────────────────
"
            f"  --pids-limit={pids} \
"
            f"  # ── File descriptors ─────────────────────────────────────────
"
            f"  --ulimit nofile={nofile[0]}:{nofile[1]} \
"
            f"  --ulimit nproc={pids}:{pids} \
"
            f"  # ── Shared memory ────────────────────────────────────────────
"
            f"  --shm-size={shm}m \
"
            f"  # ── OOM priority ─────────────────────────────────────────────
"
            f"  --oom-score-adj={oom} \
"
            f"  # ── Restart policy ───────────────────────────────────────────
"
            f"  --restart=always \
"
            f"  # ── Network ──────────────────────────────────────────────────
"
            f"  {net_flag} \
"
            f"  # ── Security ─────────────────────────────────────────────────
"
            f"{sec_lines}
"
            f"  # ── Runtime ──────────────────────────────────────────────────
"
            f"  --cgroups={'enabled' if inp.cgroup_version == 'v2' else 'no-conmon'} \
"
            f"  --log-driver=journald \
"
            f"  <IMAGE> [CMD]
"
        )

    # ── quadlet unit renderer ─────────────────────────────────────────────────

    def _render_quadlet(self) -> str:
        inp    = self.inp
        quota  = self._cpu_quota()
        mem    = self._mem_mb()
        swap   = self._mem_swap_mb()
        res    = self._mem_reservation_mb()
        pids   = self._pids_limit()
        nofile = self._nofile()
        shm    = self._shm_mb()
        oom    = self._oom_score()

        caps = ""
        if inp.drop_all_caps:
            caps = (
                "DropCapability=ALL
"
                "AddCapability=NET_BIND_SERVICE
"
                + ("AddCapability=IPC_LOCK
" if inp.container_type == "database" else "")
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Podman Quadlet  [{inp.mode.value.upper():8s}]  "
            f"type={inp.container_type}  Podman 4.4+  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Location: ~/.config/containers/systemd/<name>.container  (rootless)
"
            f"#        or: /etc/containers/systemd/<name>.container       (root)
"
            f"# Activate: systemctl --user daemon-reload && systemctl --user start <name>

"
            f"[Unit]
"
            f"Description=VAREX managed container — {inp.container_type}
"
            f"After=network-online.target
"
            f"Wants=network-online.target

"
            f"[Container]
"
            f"Image=<IMAGE>
"
            f"ContainerName=varex-{inp.container_type}

"
            f"# ── CPU
"
            f"CPUQuota={int(inp.container_cpu_cores * 100)}%
"
            f"CPUShares=1024

"
            f"# ── Memory
"
            f"Memory={mem}M
"
            f"MemorySwap={swap}M
"
            f"MemoryReservation={res}M

"
            f"# ── PIDs
"
            f"PidsLimit={pids}

"
            f"# ── Ulimits
"
            f"Ulimit=nofile={nofile[0]}:{nofile[1]}
"
            f"Ulimit=nproc={pids}:{pids}

"
            f"# ── Shared memory
"
            f"ShmSize={shm}M

"
            f"# ── OOM
"
            f"OOMScoreAdjust={oom}

"
            f"# ── Network
"
            f"Network={inp.network_mode}.network

"
            f"# ── Security
"
            f"{caps}"
            f"NoNewPrivileges=true
"
            + ("ReadOnly=true
" if inp.read_only_rootfs else "") +
            + ("UserNS=keep-id
" if inp.rootless else "") +
            f"
# ── Logging
"
            f"LogDriver=journald

"
            f"[Service]
"
            f"Restart=always
"
            f"TimeoutStartSec=90
"
            f"TimeoutStopSec=30

"
            f"[Install]
"
            f"WantedBy=default.target
"
        )

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self) -> list:
        inp    = self.inp
        p      = self._p
        ex     = inp.existing
        quota  = self._cpu_quota()
        mem    = self._mem_mb()
        swap   = self._mem_swap_mb()
        res    = self._mem_reservation_mb()
        pids   = self._pids_limit()
        nofile = self._nofile()
        shm    = self._shm_mb()
        oom    = self._oom_score()

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "--memory (hard limit)", f"{mem}m", M,
                f"Container RAM hard limit = {mem}MB = {inp.container_ram_gb}GB. "
                "When container exceeds --memory: OOM killer sends SIGKILL immediately. "
                "Without --memory: container can consume ALL host RAM → host OOM. "
                "In multi-container hosts: one container starves all others without limits. "
                f"cgroup v2: memory.max = {mem}M (atomic, no gap between limit and OOM).",
                f"--memory={mem}m",
                f"{ex.memory_mb}m" if ex.memory_mb else "NOT SET",
                safe=not bool(ex.memory_mb),
            ),
            p(
                "--cpus (CPU limit)", str(inp.container_cpu_cores), M,
                f"CPU limit = {inp.container_cpu_cores} cores = "
                f"quota {quota}μs / period {_CPU_PERIOD}μs. "
                "Without --cpus: container can burst to 100% of ALL host CPUs "
                "→ CPU starvation for other containers. "
                "cgroup v2: cpu.max = '{quota} {_CPU_PERIOD}'. "
                "--cpu-shares=1024 (relative weight, only active under CPU contention).",
                f"--cpus={inp.container_cpu_cores} --cpu-shares=1024",
                str(ex.cpus) if ex.cpus else "NOT SET",
                safe=not bool(ex.cpus),
            ),
            p(
                "--memory-swap", f"{swap}m", M,
                f"Memory + swap limit = {swap}MB. "
                + (
                    f"database/cache: swap={swap}MB = memory={mem}MB "
                    "(effectively ZERO swap). "
                    "Databases MUST NOT swap: swapped DB pages cause 1000x latency spikes. "
                    "PostgreSQL shared_buffers, Redis in-memory: swap = instant performance collapse."
                    if inp.container_type in ("database", "cache") else
                    f"--memory-swap={swap}MB = {mem}MB RAM + {swap - mem}MB swap headroom. "
                    "Allows container to use up to 1× its RAM in swap before OOM kill. "
                    "Prevents sudden OOM kill during brief memory spikes."
                ),
                f"--memory-swap={swap}m",
                f"{ex.memory_swap_mb}m" if ex.memory_swap_mb else None,
            ),
            p(
                "--pids-limit", str(pids), M,
                f"Process/thread limit = {pids} = max(expected_pids({inp.expected_pids})×2, 512). "
                "Default -1 = unlimited: a single container can fork-bomb the host "
                "by exhausting the kernel PID table. "
                "All containers on host share the same PID namespace. "
                f"Fork bomb protection: container with pids-limit={pids} "
                "cannot create more than {pids} total processes + threads.",
                f"--pids-limit={pids}",
                str(ex.pids_limit) if ex.pids_limit and ex.pids_limit != -1 else "UNLIMITED (-1)",
                safe=bool(ex.pids_limit == -1) if ex.pids_limit is not None else False,
            ),
            p(
                "--ulimit nofile", f"{nofile[0]}:{nofile[1]}", M,
                f"File descriptor limit = {nofile[0]} (soft) : {nofile[1]} (hard). "
                + (
                    "database/cache: 1,048,576 FDs. "
                    "PostgreSQL: 1 FD per connection + WAL files + data files. "
                    "Redis: 1 FD per client connection. "
                    "Default 1024 → OOM-style errors at 1025th connection."
                    if inp.container_type in ("database", "cache") else
                    "web/worker: 65,535 FDs. "
                    "NGINX: 1 FD per connection × 2 (upstream + downstream). "
                    "Default 1024 → 'Too many open files' error at 513th connection."
                ),
                f"--ulimit nofile={nofile[0]}:{nofile[1]}",
                ex.ulimit_nofile,
                safe=False,
            ),
            p(
                "--security-opt no-new-privileges", "enabled", M,
                "Prevents container processes from gaining additional Linux capabilities "
                "via setuid binaries or file capabilities. "
                "Without: a setuid-root binary inside container can escalate to root on host. "
                "This is a defense-in-depth measure — container root ≠ host root in rootless mode "
                "but still critical for root-mode containers.",
                "--security-opt=no-new-privileges",
                None if not ex.security_opt else
                "SET" if "no-new-privileges" in " ".join(ex.security_opt) else "NOT SET",
                safe=False,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "--cap-drop=ALL", "enabled", MED,
                "Drop ALL Linux capabilities, add back only required. "
                "Default container: retains ~14 capabilities including NET_ADMIN, SYS_PTRACE. "
                "Principle of least privilege: container only needs NET_BIND_SERVICE "
                "(bind port < 1024) for web containers. "
                "Database: also needs IPC_LOCK (mlock shared_buffers). "
                "Reduces attack surface: even if container process is compromised, "
                "no capabilities to escalate.",
                "--cap-drop=ALL --cap-add=NET_BIND_SERVICE",
            ) if inp.drop_all_caps else None,
            p(
                "--memory-reservation (soft limit)", f"{res}m", MED,
                f"Memory soft limit = {res}MB = memory_limit × 80%. "
                "Soft limit: container is guaranteed {res}MB even under host memory pressure. "
                "When host is low on memory, kernel reclaims pages from containers "
                "above their reservation first. "
                "Prevents well-behaved containers from being OOM-killed "
                "when a noisy neighbour is the actual pressure source.",
                f"--memory-reservation={res}m",
                f"{ex.memory_reservation_mb}m" if ex.memory_reservation_mb else None,
            ),
            p(
                "--shm-size", f"{shm}m", MED,
                f"/dev/shm = {shm}MB. "
                + (
                    f"database: /dev/shm = container_ram × 25% = {shm}MB. "
                    "PostgreSQL uses /dev/shm for shared_buffers POSIX shared memory. "
                    "Default /dev/shm in containers = 64MB. "
                    "PostgreSQL shared_buffers > 64MB → 'could not resize shared memory segment' error."
                    if inp.container_type in ("database", "cache") else
                    f"Default 64MB is sufficient for most web/worker containers."
                ),
                f"--shm-size={shm}m",
                f"{ex.shm_size_mb}m" if ex.shm_size_mb else None,
            ),
            p(
                "--oom-score-adj", str(oom), MED,
                f"OOM kill priority = {oom}. "
                + {
                    "batch":    "batch jobs (+500): killed first under memory pressure — protects long-running services.",
                    "database": "database (-500): killed last — losing a DB process is catastrophic.",
                    "cache":    "cache (-300): protected — losing cache causes cache stampede.",
                    "web":      "web (0): default priority — killed proportionally to memory usage.",
                    "worker":   "worker (0): default priority.",
                }.get(inp.container_type, ""),
                f"--oom-score-adj={oom}",
                str(ex.oom_score_adj) if ex.oom_score_adj is not None else None,
            ),
            p(
                "Rootless mode", str(inp.rootless), MED,
                "Rootless: containers run as non-root user (user namespace remapping). "
                "Container UID 0 maps to host unprivileged UID. "
                "Even if container is fully compromised: attacker has only unprivileged host UID. "
                "Limitations: --network=bridge requires slirp4netns or pasta (user-space TCP stack). "
                "Recommended: rootless for all non-database containers. "
                "Rootful required for: containers that need real root (mlock, CAP_NET_ADMIN).",
                "--userns=keep-id (rootless)" if inp.rootless else "# rootful: no --userns flag",
            ),
            p(
                "cgroup v2", inp.cgroup_version, MED,
                "cgroup v2: unified hierarchy — single cgroup tree for all controllers. "
                "memory.max: atomic hard limit (no 'memory + swap' confusion of cgroup v1). "
                "cpu.max: precise CPU throttling with guaranteed BW controller. "
                "cgroup v1: separate memory and cpu hierarchies — race conditions possible. "
                "RHEL 9 / Ubuntu 22.04+: cgroup v2 default. "
                "Rootless Podman: cgroup v2 required for full resource limit enforcement.",
                "# RHEL 9 default: cgroup v2
"
                "# Verify: stat -f /sys/fs/cgroup | grep -i type",
                str(ex.cgroup_v2) if ex.cgroup_v2 is not None else None,
            ),
            p(
                "--restart=always", "always", MED,
                "Container restarts automatically after crash or host reboot. "
                "Podman with systemd: use Quadlet unit with Restart=always in [Service]. "
                "Podman without systemd: --restart=always only works with podman service "
                "(rootless: loginctl enable-linger). "
                "Without restart policy: container stops on crash, stays down until manual start.",
                "--restart=always  # or Restart=always in Quadlet [Service]",
                ex.restart_policy,
            ),
            p(
                "--read-only rootfs", str(inp.read_only_rootfs), MED,
                "Mount container root filesystem read-only. "
                "Prevents runtime writes to container image layers. "
                "Any file write attempt → Permission denied (unless tmpfs mount). "
                "Security benefit: malware cannot persist to container filesystem. "
                "Use --tmpfs /tmp --tmpfs /var/run for writable temp directories.",
                "--read-only --tmpfs /tmp --tmpfs /var/run",
            ) if inp.read_only_rootfs else None,
            p(
                "Quadlet (.container unit)", "enabled", MED,
                "Quadlet (Podman 4.4+): define containers as systemd unit files. "
                "systemd manages lifecycle: start/stop/restart/logging/dependencies. "
                "No need for docker-compose or podman generate systemd (deprecated). "
                "Quadlet file location: ~/.config/containers/systemd/<name>.container. "
                "Reload: systemctl --user daemon-reload && systemctl --user start <name>.",
                "# See quadlet_unit in response for complete .container file",
            ) if inp.use_quadlet else None,
        ]

        # ── MINOR ─────────────────────────────────────────────────────────
        params += [
            p(
                "--log-driver=journald", "journald", MIN,
                "Container logs routed to systemd journal. "
                "Enables: journalctl -u <service> filtering, log rotation via logrotate, "
                "structured logging with container metadata. "
                "Alternative: --log-driver=k8s-file for Kubernetes compatibility.",
                "--log-driver=journald",
            ),
            p(
                "podman healthcheck", "recommended", MIN,
                "Define HEALTHCHECK in Dockerfile or via --health-cmd. "
                "Podman marks container healthy/unhealthy — "
                "systemd Restart=on-failure can restart on unhealthy state. "
                "Essential for: web containers behind load balancer, "
                "database containers that need readiness signalling.",
                "HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
"
                "  CMD curl -f http://localhost:8080/health || exit 1",
            ),
            p(
                "loginctl enable-linger (rootless)", "required", MIN,
                "Rootless containers stopped when user logs out without linger. "
                "enable-linger: user systemd session persists after logout. "
                "Required for production rootless containers.",
                f"loginctl enable-linger $USER",
            ) if inp.rootless else None,
        ]

        return [x for x in params if x is not None]

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if not ex.memory_mb:
            findings.append(
                "[MAJOR] --memory NOT SET. Container can consume ALL host RAM. "
                f"Recommended: --memory={self._mem_mb()}m"
            )
        if not ex.cpus and not ex.cpu_quota:
            findings.append(
                "[MAJOR] --cpus NOT SET. Container can burst to 100% of all host CPUs. "
                f"Recommended: --cpus={self.inp.container_cpu_cores}"
            )
        if ex.pids_limit == -1 or ex.pids_limit is None:
            findings.append(
                "[MAJOR] --pids-limit=-1 (unlimited). Fork bomb can exhaust host PID table. "
                f"Recommended: --pids-limit={self._pids_limit()}"
            )
        if ex.ulimit_nofile == "1024:1024" or ex.ulimit_nofile is None:
            findings.append(
                f"[MAJOR] ulimit nofile=1024 — too low. "
                f"Recommended: {self._nofile()[0]}:{self._nofile()[1]}. "
                "'Too many open files' errors will occur at 513th connection."
            )
        if not ex.security_opt or "no-new-privileges" not in " ".join(ex.security_opt):
            findings.append(
                "[MAJOR] --security-opt=no-new-privileges NOT SET. "
                "Container processes can gain capabilities via setuid binaries."
            )
        if ex.rootless is False and self.inp.rootless:
            findings.append(
                "[MEDIUM] Container running as root (rootful). "
                "Switch to rootless (--userns=keep-id) to limit blast radius of compromise."
            )
        if ex.cgroup_v2 is False:
            findings.append(
                "[MEDIUM] cgroup v1 detected. Memory limits have known race conditions. "
                "Upgrade host to RHEL 9 / Ubuntu 22.04+ for cgroup v2."
            )
        if ex.restart_policy in (None, "no"):
            findings.append(
                "[MEDIUM] restart_policy='no'. Container stays down after crash or reboot. "
                "Set --restart=always or use Quadlet with Restart=always."
            )
        if not ex.security_opt or "drop" not in " ".join(ex.security_opt).lower():
            findings.append(
                "[MEDIUM] --cap-drop=ALL not set. Container retains default capabilities "
                "including potentially dangerous ones (SYS_PTRACE, NET_ADMIN). "
                "Add --cap-drop=ALL --cap-add=<only-required>."
            )
        if self.inp.container_type in ("database", "cache"):
            if ex.memory_swap_mb == -1 or (ex.memory_swap_mb and ex.memory_swap_mb > (ex.memory_mb or 0) * 2):
                findings.append(
                    f"[MAJOR] database/cache container with swap enabled (memory_swap={ex.memory_swap_mb}m). "
                    "Database swap causes catastrophic latency. "
                    f"Set --memory-swap={self._mem_mb()}m (= --memory, disables swap)."
                )

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> PodmanOutput:
        nofile = self._nofile()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.host_cpu_cores,
            ram_gb    = self.inp.host_ram_gb,
            max_conns = self.inp.expected_pids * 4,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.sysctls),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        return PodmanOutput(
            mode                    = self.inp.mode,
            cpu_quota               = self._cpu_quota(),
            cpu_period              = _CPU_PERIOD,
            memory_limit_mb         = self._mem_mb(),
            memory_swap_limit_mb    = self._mem_swap_mb(),
            memory_reservation_mb   = self._mem_reservation_mb(),
            pids_limit              = self._pids_limit(),
            ulimit_nofile_soft      = nofile[0],
            ulimit_nofile_hard      = nofile[1],
            shm_size_mb             = self._shm_mb(),
            podman_run_flags        = self._render_run_flags(),
            quadlet_unit            = self._render_quadlet() if self.inp.use_quadlet
                                      else "# use_quadlet=False: quadlet not generated",
            major_params            = major,
            medium_params           = medium,
            minor_params            = minor,
            os_sysctl_conf          = os_engine.sysctl_block(),
            ha_suggestions=[
                "Run multiple container replicas on different hosts behind NGINX/HAProxy.",
                "Use Podman pods (shared network namespace) to co-locate sidecar containers "
                "(log collector, metrics exporter) without bridge network overhead.",
                "Podman Quadlet + systemd: use After= / Requires= dependencies for ordered startup.",
                "Use podman-compose for multi-container orchestration on single host.",
                "For multi-host: migrate to Kubernetes (k8s) or OpenShift — "
                "Podman Quadlet files are structurally compatible with k8s Pod specs.",
                "Registry: use podman login + pull from private registry "
                "(Quay.io, Harbor, ECR) with pull secrets.",
            ],
            performance_warnings=[w for w in [
                (f"container_ram_gb ({self.inp.container_ram_gb}GB) > host_ram_gb × 80% "
                 f"({self.inp.host_ram_gb * 0.8:.1f}GB). "
                 "Host OOM likely under memory pressure.")
                if self.inp.container_ram_gb > self.inp.host_ram_gb * 0.8 else None,
                ("network_mode=bridge with rootless: uses slirp4netns or pasta "
                 "(user-space TCP stack). "
                 "High-throughput workloads: use --network=host for zero NAT overhead.")
                if self.inp.rootless and self.inp.network_mode == "bridge" else None,
                ("cgroup_version=v1: memory limits have race conditions. "
                 "Upgrade host OS to get cgroup v2.")
                if self.inp.cgroup_version == "v1" else None,
                ("read_only_rootfs=False: container can write to image layers. "
                 "Security risk: malware can persist across container restarts.")
                if not self.inp.read_only_rootfs else None,
            ] if w],
            capacity_warning        = None,
            audit_findings          = self._audit()
                                      if self.inp.mode == CalcMode.EXISTING else [],
        )
