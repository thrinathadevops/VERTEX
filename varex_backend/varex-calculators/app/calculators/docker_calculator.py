"""
app/calculators/docker_calculator.py
=====================================
Docker daemon tuning calculator — NEW and EXISTING modes.

Daemon configuration via /etc/docker/daemon.json.
Container-level resource limits (cgroup) are covered by the Podman calculator.
"""
from __future__ import annotations

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.docker import DockerInput, DockerOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class DockerCalculator(BaseCalculator):

    def __init__(self, inp: DockerInput) -> None:
        self._require_positive(inp.cpu_cores,       "cpu_cores")
        self._require_positive(inp.ram_gb,           "ram_gb")
        self._require_positive(inp.container_count,  "container_count")
        self.inp = inp

    def _nofile_limit(self) -> int:
        return max(65536, self.inp.container_count * 4096)

    def _max_concurrent_downloads(self) -> int:
        return max(3, self.inp.cpu_cores)

    def _log_max_size(self) -> str:
        return "50m"

    def _log_max_file(self) -> int:
        return 5

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        nf   = self._nofile_limit()
        mcd  = self._max_concurrent_downloads()

        params = [
            p(
                "storage-driver", "overlay2", M,
                "overlay2 is the recommended production storage driver. "
                "devicemapper: deprecated, poor performance, complex setup. "
                "aufs: deprecated, not in mainline kernel. "
                "overlay2 requires Linux 4.0+ and xfs/ext4 with d_type=true.",
                '"storage-driver": "overlay2"',
                ex.storage_driver,
            ),
            p(
                "log-driver + log-opts", "json-file with rotation", M,
                "Default json-file log driver with NO rotation fills disk infinitely. "
                f"max-size={self._log_max_size()}: rotate after 50MB. "
                f"max-file={self._log_max_file()}: keep 5 files = 250MB max per container. "
                f"With {inp.container_count} containers: max {inp.container_count * 250}MB total logs.",
                f'"log-driver": "json-file",\n'
                f'"log-opts": {{\n'
                f'  "max-size": "{self._log_max_size()}",\n'
                f'  "max-file": "{self._log_max_file()}"\n'
                f'}}',
                ex.log_driver,
            ),
            p(
                "live-restore", "true", M,
                "Keep containers running when Docker daemon restarts. "
                "Without this: daemon restart/upgrade kills ALL running containers. "
                "Critical for production — allows dockerd upgrades without downtime.",
                '"live-restore": true',
                str(ex.live_restore).lower(),
            ),
            p(
                "default-ulimits (nofile)", str(nf), M,
                f"Default nofile limit for all containers = {nf}. "
                f"Formula: max(65536, container_count × 4096) = {nf}. "
                "Default 1024 causes 'too many open files' under load in web/database containers.",
                f'"default-ulimits": {{\n'
                f'  "nofile": {{\n'
                f'    "Name": "nofile",\n'
                f'    "Hard": {nf},\n'
                f'    "Soft": {nf}\n'
                f'  }}\n'
                f'}}',
                str(ex.default_ulimits_nofile) if ex.default_ulimits_nofile else None,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "userland-proxy", "false", MED,
                "Disable userland proxy for published ports. "
                "Default: docker-proxy (userspace) copies packets between host and container. "
                "With userland-proxy=false: iptables NAT handles forwarding (kernel-space, ~10x faster). "
                "Only needed on systems where iptables is broken (very rare).",
                '"userland-proxy": false',
                str(ex.userland_proxy).lower(),
            ),
            p(
                "max-concurrent-downloads", str(mcd), MED,
                f"Parallel image layer downloads = cpu_cores = {mcd}. "
                "Default 3 is slow for large images on fast networks.",
                f'"max-concurrent-downloads": {mcd}',
                str(ex.max_concurrent_downloads) if ex.max_concurrent_downloads else None,
            ),
            p(
                "max-concurrent-uploads", str(mcd), MED,
                f"Parallel image layer uploads = {mcd}.",
                f'"max-concurrent-uploads": {mcd}',
                str(ex.max_concurrent_uploads) if ex.max_concurrent_uploads else None,
            ),
            p(
                "default-address-pools", "172.17.0.0/12", MED,
                "Customize Docker network CIDR to avoid conflicts with corporate/VPN networks. "
                "Default 172.17.0.0/16 often conflicts with internal networks.",
                '"default-address-pools": [\n'
                '  {"base": "172.17.0.0/12", "size": 24}\n'
                ']',
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "metrics-addr", "0.0.0.0:9323", MIN,
                "Expose Prometheus metrics. Essential for monitoring container lifecycle, "
                "build performance, and daemon health.",
                '"metrics-addr": "0.0.0.0:9323",\n"experimental": true',
            ),
            p(
                "iptables + ip6tables", "true", MIN,
                "Let Docker manage iptables rules. Required for container networking. "
                "Only disable if using an external firewall manager.",
                '"iptables": true,\n"ip6tables": true',
            ),
            p(
                "no-new-privileges", "true", MIN,
                "Security: prevent containers from gaining new privileges via setuid/setgid binaries. "
                "Defense-in-depth hardening.",
                '"no-new-privileges": true',
            ),
        ]

        if inp.registry_mirror:
            params.append(
                p(
                    "registry-mirrors", inp.registry_mirror, MIN,
                    "Pull-through registry cache reduces bandwidth and improves pull speed.",
                    f'"registry-mirrors": ["{inp.registry_mirror}"]',
                )
            )

        return [x for x in params if x is not None]

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.storage_driver and ex.storage_driver not in ("overlay2",):
            findings.append(
                f"[MAJOR] storage-driver={ex.storage_driver}. "
                "Use overlay2 — all other drivers are deprecated or slower."
            )
        if not ex.live_restore:
            findings.append(
                "[MAJOR] live-restore=false. Docker daemon restart kills all containers."
            )
        if ex.log_driver == "json-file" and not ex.log_max_size:
            findings.append(
                "[MAJOR] json-file log driver with no max-size. "
                "Container logs will fill disk infinitely."
            )
        if ex.default_ulimits_nofile and ex.default_ulimits_nofile < 65536:
            findings.append(
                f"[MEDIUM] default nofile ulimit={ex.default_ulimits_nofile}. "
                "Web/database containers will hit 'too many open files'. Set to 65536+."
            )
        if ex.userland_proxy:
            findings.append(
                "[MEDIUM] userland-proxy=true. Using slower userspace port forwarding. "
                "Set to false for iptables-based forwarding."
            )

        return findings

    def _render_conf(self) -> str:
        inp = self.inp
        nf  = self._nofile_limit()
        mcd = self._max_concurrent_downloads()

        mirror_line = ""
        if inp.registry_mirror:
            mirror_line = f'\n  "registry-mirrors": ["{inp.registry_mirror}"],'

        return (
            '{\n'
            f'  "storage-driver": "overlay2",\n'
            f'  "log-driver": "json-file",\n'
            f'  "log-opts": {{\n'
            f'    "max-size": "{self._log_max_size()}",\n'
            f'    "max-file": "{self._log_max_file()}"\n'
            f'  }},\n'
            f'  "live-restore": true,\n'
            f'  "userland-proxy": false,\n'
            f'  "max-concurrent-downloads": {mcd},\n'
            f'  "max-concurrent-uploads": {mcd},\n'
            f'  "default-ulimits": {{\n'
            f'    "nofile": {{\n'
            f'      "Name": "nofile",\n'
            f'      "Hard": {nf},\n'
            f'      "Soft": {nf}\n'
            f'    }}\n'
            f'  }},\n'
            f'  "no-new-privileges": true,\n'
            f'  "metrics-addr": "0.0.0.0:9323",\n'
            f'  "experimental": true,\n'
            f'  "iptables": true,\n'
            f'  "ip6tables": true'
            f'{mirror_line}\n'
            '}\n'
        )

    def generate(self) -> DockerOutput:
        nf = self._nofile_limit()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = self.inp.container_count * 100,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            "Use Docker Swarm or Kubernetes for multi-host container orchestration.",
            "Deploy Watchtower for automated container image updates.",
            "Use Docker Compose for multi-container application definitions.",
            "Implement health checks in Dockerfile: HEALTHCHECK CMD curl -f http://localhost/ || exit 1.",
        ]

        perf_warnings = [w for w in [
            (f"container_count={self.inp.container_count} is high. "
             "Ensure sufficient file descriptors and cgroup limits.")
            if self.inp.container_count > 100 else None,
        ] if w]

        return DockerOutput(
            mode               = self.inp.mode,
            storage_driver     = "overlay2",
            log_config         = f"json-file (max-size={self._log_max_size()}, max-file={self._log_max_file()})",
            recommended_ulimits = nf,
            daemon_json_snippet = self._render_conf(),
            major_params       = major,
            medium_params      = medium,
            minor_params       = minor,
            os_sysctl_conf     = os_engine.sysctl_block(),
            ha_suggestions     = ha_suggestions,
            performance_warnings = perf_warnings,
            capacity_warning   = self._capacity_warning(
                self.inp.container_count, 200, "Docker container count"
            ),
            audit_findings     = self._audit()
                                 if self.inp.mode == CalcMode.EXISTING else [],
        )
