"""
app/calculators/haproxy_calculator.py
======================================
HAProxy tuning calculator — NEW and EXISTING modes.

Connection capacity formula
---------------------------
global maxconn = min(ram_mb / 20, 200000)   ~20KB per connection
frontend maxconn = global_maxconn × 80%
nbthread = cpu_cores
"""
from __future__ import annotations

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.haproxy import HAProxyInput, HAProxyOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class HAProxyCalculator(BaseCalculator):

    def __init__(self, inp: HAProxyInput) -> None:
        self._require_positive(inp.cpu_cores,           "cpu_cores")
        self._require_positive(inp.ram_gb,               "ram_gb")
        self._require_positive(inp.expected_concurrent,  "expected_concurrent")
        self.inp = inp

    def _global_maxconn(self) -> int:
        ram_mb = int(self.inp.ram_gb * 1024)
        return min(ram_mb // 20, 200000)

    def _frontend_maxconn(self) -> int:
        return int(self._global_maxconn() * 0.80)

    def _nbthread(self) -> int:
        return self.inp.cpu_cores

    def _maxqueue(self) -> int:
        return max(100, self._global_maxconn() // max(self.inp.backend_count, 1))

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        gmc  = self._global_maxconn()
        fmc  = self._frontend_maxconn()
        nbt  = self._nbthread()
        mq   = self._maxqueue()

        params = [
            p(
                "global maxconn", str(gmc), M,
                f"Global connection limit = min(RAM_MB/20, 200000) = {gmc}. "
                f"Each connection uses ~20KB (kernel buffers + HAProxy state). "
                f"At {gmc} connections: ~{gmc * 20 // 1024}MB RAM. "
                "Beyond this, HAProxy drops new connections with 503.",
                f"global\n    maxconn {gmc}",
                str(ex.global_maxconn) if ex.global_maxconn else None,
            ),
            p(
                "nbthread", str(nbt), M,
                f"Worker threads = cpu_cores = {nbt}. "
                "HAProxy 2.5+ uses multi-threading instead of nbproc. "
                "Each thread handles connections independently with minimal lock contention.",
                f"global\n    nbthread {nbt}",
                str(ex.nbthread) if ex.nbthread else None,
                safe=False,
            ),
            p(
                "frontend maxconn", str(fmc), M,
                f"Per-frontend connection limit = global × 80% = {fmc}. "
                "Reserves 20% of global capacity for backend health checks and admin socket.",
                f"frontend http-in\n    maxconn {fmc}",
                str(ex.frontend_maxconn) if ex.frontend_maxconn else None,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "timeout connect", "5s", MED,
                "Max time to establish connection to backend server. "
                "5s is generous — if backend can't accept in 5s, it's likely down. "
                "Too long → slow failure detection → poor user experience.",
                "defaults\n    timeout connect 5s",
                ex.timeout_connect,
            ),
            p(
                "timeout client", "30s", MED,
                "Max inactivity time from client side. "
                "30s balances keep-alive reuse vs resource consumption. "
                "For WebSocket: increase to 3600s.",
                "defaults\n    timeout client 30s",
                ex.timeout_client,
            ),
            p(
                "timeout server", "30s", MED,
                "Max inactivity time from server side. "
                "Match to your application's longest expected response time. "
                "For API backends: 30s. For file uploads: increase accordingly.",
                "defaults\n    timeout server 30s",
                ex.timeout_server,
            ),
            p(
                "option httpchk", "GET /health", MED,
                "HTTP health checks instead of TCP-only. "
                "TCP checks only verify port is open — the app could be deadlocked. "
                "HTTP checks verify the application is actually responding.",
                "backend servers\n    option httpchk GET /health\n"
                "    http-check expect status 200",
            ),
            p(
                "retries", "3", MED,
                "Retry failed connections to backend 3 times before marking server down. "
                "Combined with redispatch: HAProxy retries on a different server.",
                "defaults\n    retries 3\n    option redispatch",
            ),
            p(
                "maxqueue", str(mq), MED,
                f"Per-server queue depth = global_maxconn / backends = {mq}. "
                "Requests beyond maxqueue return 503 immediately. "
                "Prevents request pileup when a backend is slow.",
                f"backend servers\n    default-server maxqueue {mq}",
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "stats enable", "recommended", MIN,
                "Enable HAProxy stats page for monitoring. "
                "Accessible at /haproxy-stats. Must be password-protected.",
                "listen stats\n    bind :8404\n    stats enable\n"
                "    stats uri /haproxy-stats\n    stats auth admin:YourPassword",
                "enabled" if ex.stats_enabled else "disabled",
            ),
            p(
                "log global + option httplog", "recommended", MIN,
                "Request-level logging with full HTTP details. "
                "Without httplog: only connection-level logging (miss request path, status code).",
                "defaults\n    log global\n    option httplog\n    option dontlognull",
            ),
            p(
                "ssl-default-bind-ciphers", "modern TLS", MIN,
                "Restrict to TLS 1.2+ with strong cipher suites. "
                "Disable SSLv3, TLS 1.0, TLS 1.1.",
                "global\n    ssl-default-bind-options ssl-min-ver TLSv1.2\n"
                "    ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384",
            ) if inp.ssl_enabled else None,
        ]

        return [x for x in params if x is not None]

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.nbthread is not None and ex.nbthread < self.inp.cpu_cores:
            findings.append(
                f"[MAJOR] nbthread={ex.nbthread}, but cpu_cores={self.inp.cpu_cores}. "
                "HAProxy is under-utilizing available CPU."
            )
        if ex.global_maxconn and ex.global_maxconn < self.inp.expected_concurrent:
            findings.append(
                f"[MAJOR] global maxconn={ex.global_maxconn} < expected concurrent "
                f"connections ({self.inp.expected_concurrent}). Connections will be dropped."
            )
        if not ex.stats_enabled:
            findings.append(
                "[MEDIUM] Stats page disabled. No visibility into backend health, "
                "queue depth, or error rates."
            )
        if not ex.ssl_enabled and self.inp.ssl_enabled:
            findings.append(
                "[MEDIUM] SSL/TLS not configured on HAProxy frontend."
            )

        return findings

    def _render_conf(self) -> str:
        inp = self.inp
        gmc = self._global_maxconn()
        fmc = self._frontend_maxconn()
        nbt = self._nbthread()

        ssl_block = ""
        if inp.ssl_enabled:
            ssl_block = (
                "    bind :443 ssl crt /etc/haproxy/certs/ alpn h2,http/1.1\n"
                "    http-request redirect scheme https unless { ssl_fc }\n"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗\n"
            f"# ║  VAREX haproxy.cfg  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}        ║\n"
            f"# ╚══════════════════════════════════════════════════════════════╝\n\n"
            f"global\n"
            f"    maxconn {gmc}\n"
            f"    nbthread {nbt}\n"
            f"    log /dev/log local0\n"
            f"    ssl-default-bind-options ssl-min-ver TLSv1.2\n"
            f"    tune.ssl.default-dh-param 2048\n\n"
            f"defaults\n"
            f"    mode {inp.http_mode}\n"
            f"    log global\n"
            f"    option httplog\n"
            f"    option dontlognull\n"
            f"    timeout connect 5s\n"
            f"    timeout client  30s\n"
            f"    timeout server  30s\n"
            f"    retries 3\n"
            f"    option redispatch\n\n"
            f"frontend http-in\n"
            f"    bind :80\n"
            f"{ssl_block}"
            f"    maxconn {fmc}\n"
            f"    default_backend servers\n\n"
            f"backend servers\n"
            f"    balance roundrobin\n"
            f"    option httpchk GET /health\n"
            f"    http-check expect status 200\n"
            f"    default-server check inter 5s fall 3 rise 2\n"
            + "".join(
                f"    server app{i+1} 10.0.0.{10+i}:8080 check\n"
                for i in range(min(inp.backend_count, 8))
            ) +
            f"\nlisten stats\n"
            f"    bind :8404\n"
            f"    stats enable\n"
            f"    stats uri /haproxy-stats\n"
            f"    stats auth admin:ChangeMe\n"
        )

    def generate(self) -> HAProxyOutput:
        gmc = self._global_maxconn()
        fmc = self._frontend_maxconn()
        nbt = self._nbthread()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = gmc,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            "Deploy HAProxy in active-passive with keepalived for VIP failover.",
            "Use stick-tables for session persistence across reloads.",
            "Enable runtime API socket for zero-downtime config changes.",
            "Monitor via Prometheus exporter on /metrics endpoint.",
        ]

        perf_warnings = [w for w in [
            (f"expected_concurrent ({self.inp.expected_concurrent}) > global_maxconn ({gmc}). "
             "Add more RAM or reduce concurrent connections.")
            if self.inp.expected_concurrent > gmc else None,
        ] if w]

        return HAProxyOutput(
            mode               = self.inp.mode,
            global_maxconn     = gmc,
            frontend_maxconn   = fmc,
            nbthread           = nbt,
            haproxy_cfg_snippet = self._render_conf(),
            major_params       = major,
            medium_params      = medium,
            minor_params       = minor,
            os_sysctl_conf     = os_engine.sysctl_block(),
            ha_suggestions     = ha_suggestions,
            performance_warnings = perf_warnings,
            capacity_warning   = self._capacity_warning(
                self.inp.expected_concurrent, gmc, "HAProxy maxconn"
            ),
            audit_findings     = self._audit()
                                 if self.inp.mode == CalcMode.EXISTING else [],
        )
