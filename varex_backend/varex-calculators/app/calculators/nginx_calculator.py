from __future__ import annotations
import math
from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.core.models import TuningParam
from app.schemas.nginx import NginxInput, NginxOutput

M, MED, MIN = ImpactLevel.MAJOR, ImpactLevel.MEDIUM, ImpactLevel.MINOR


class NginxCalculator(BaseCalculator):
    _MEM_PER_CONN_KB:   float = 16.0
    _SSL_OVERHEAD_KB:   float = 64.0
    _MAX_WORKER_CONNS:  int   = 65_535
    _PROXY_FD_FACTOR:   int   = 4

    def __init__(self, inp: NginxInput) -> None:
        self._require_positive(inp.cpu_cores,       "cpu_cores")
        self._require_positive(inp.ram_gb,          "ram_gb")
        self._require_positive(inp.expected_rps,    "expected_rps")
        self._require_positive(inp.avg_response_kb, "avg_response_kb")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────
    def _mem_per_conn_kb(self) -> float:
        base = self._MEM_PER_CONN_KB + self.inp.avg_response_kb
        if self.inp.ssl_enabled:
            base += self._SSL_OVERHEAD_KB
        return base

    def _worker_processes(self) -> int:
        return self.inp.cpu_cores

    def _worker_connections(self) -> int:
        ram_per_worker_kb = (self.inp.ram_gb * 1024 * 1024) / self.inp.cpu_cores
        raw = math.floor(ram_per_worker_kb / self._mem_per_conn_kb())
        return max(512, min(raw, self._MAX_WORKER_CONNS))

    def _rlimit(self) -> int:
        return self._worker_connections() * 2

    def _keepalive_timeout(self) -> int:
        if not self.inp.keepalive_enabled:
            return 0
        base = 65 if self.inp.ssl_enabled else 30
        if self.inp.expected_rps > 10_000:
            return max(10, base - 20)
        return base

    def _client_max_body_size(self) -> str:
        size_mb = max(1, min(int(self.inp.avg_response_kb * 4 / 1024), 100))
        return f"{size_mb}m"

    def _proxy_buffer_size(self) -> str:
        size_kb = max(8, 2 ** math.ceil(math.log2(max(1, self.inp.avg_response_kb))))
        return f"{int(size_kb)}k"

    def _max_clients(self, wp: int, wc: int) -> int:
        return wp * wc // self._PROXY_FD_FACTOR if self.inp.reverse_proxy else wp * wc

    # ── tiered NGINX-specific params ──────────────────────────────────────
    def _nginx_params(self, wp: int, wc: int, rl: int,
                      kt: int, cmb: str, pb: str) -> list[TuningParam]:
        ex = self.inp.existing
        cur_wp = str(ex.worker_processes)  if ex.worker_processes  else None
        cur_wc = str(ex.worker_connections) if ex.worker_connections else None
        cur_rl = str(ex.worker_rlimit_nofile) if ex.worker_rlimit_nofile else None

        return [
            # MAJOR
            self._param("worker_processes",    str(wp),  M,
                "Must equal CPU cores. Too few → CPU idle. Too many → context-switch overhead.",
                f"worker_processes {wp};", cur_wp),
            self._param("worker_connections",  str(wc),  M,
                "Max simultaneous connections per worker. "
                "Drives max_clients = worker_processes × worker_connections [/4 for proxy].",
                f"worker_connections {wc};", cur_wc),
            self._param("worker_rlimit_nofile", str(rl), M,
                "Must be ≥ worker_connections × 2 (client + upstream FDs + log files).",
                f"worker_rlimit_nofile {rl};", cur_rl),
            # MEDIUM
            self._param("use epoll",          "epoll",  MED,
                "Linux epoll is O(1) vs select/poll. Critical for high-concurrency workloads.",
                "events { use epoll; multi_accept on; }"),
            self._param("keepalive_timeout",  str(kt),  MED,
                "Balances connection reuse vs FD exhaustion. Reduce under very high RPS.",
                f"keepalive_timeout {kt};",
                str(ex.keepalive_timeout) if ex.keepalive_timeout else None),
            self._param("client_max_body_size", cmb,    MED,
                "Prevents oversized uploads from exhausting memory buffers.",
                f"client_max_body_size {cmb};",
                ex.client_max_body_size),
            self._param("sendfile",           "on",     MED,
                "Zero-copy file transfer. Significant throughput gain for static content.",
                "sendfile on;"),
            self._param("tcp_nopush",         "on",     MED,
                "Batch TCP packets to reduce header overhead on sendfile paths.",
                "tcp_nopush on;"),
            # MINOR
            self._param("open_file_cache",
                "max=200000 inactive=20s", MIN,
                "Caches file handles, stat() results. Reduces syscalls for static serving.",
                "open_file_cache max=200000 inactive=20s;"),
            self._param("gzip",               "on",     MIN,
                "CPU cost is low; bandwidth savings significant for text/API responses.",
                "gzip on; gzip_vary on; gzip_min_length 1024;"),
        ] + ([
            self._param("proxy_buffer_size",  pb, MED,
                "Buffers upstream response headers in memory. "
                "Too small forces disk temp files. Align to power-of-2.",
                f"proxy_buffer_size {pb};"),
            self._param("proxy_connect_timeout", "10s", MED,
                "Fail fast on dead upstreams rather than holding worker connections.",
                "proxy_connect_timeout 10s; proxy_read_timeout 30s;"),
            self._param("upstream keepalive", "32",    MED,
                "Reuses backend connections reducing TCP handshake overhead per request.",
                "keepalive 32;  # inside upstream {} block"),
        ] if self.inp.reverse_proxy else [])

    # ── audit (EXISTING mode) ─────────────────────────────────────────────
    def _audit(self, wp: int, wc: int, rl: int, kt: int) -> list[str]:
        findings: list[str] = []
        ex = self.inp.existing
        if ex.worker_processes and ex.worker_processes != wp:
            findings.append(
                f"worker_processes is {ex.worker_processes} but should be {wp} "
                f"(match CPU cores). {'Under-utilising CPUs.' if ex.worker_processes < wp else 'Excess context switching.'}"
            )
        if ex.worker_connections and ex.worker_connections < wc * 0.5:
            findings.append(
                f"worker_connections={ex.worker_connections} is less than half the recommended "
                f"{wc}. This severely limits concurrency."
            )
        if ex.worker_rlimit_nofile and ex.worker_rlimit_nofile < wc * 2:
            findings.append(
                f"worker_rlimit_nofile={ex.worker_rlimit_nofile} is below worker_connections×2 "
                f"({wc*2}). NGINX will hit 'too many open files' under load."
            )
        if ex.keepalive_timeout and ex.keepalive_timeout > 120:
            findings.append(
                f"keepalive_timeout={ex.keepalive_timeout}s is very high. "
                "Long-lived idle connections consume FDs and memory."
            )
        # check OS sysctl
        for key, cur_val in (ex.os_sysctl or {}).items():
            if key == "net.core.somaxconn" and int(cur_val) < 1024:
                findings.append(
                    f"OS net.core.somaxconn={cur_val} is dangerously low (default 128). "
                    "Silent connection drops under burst traffic."
                )
            if key == "vm.swappiness" and int(cur_val) > 30:
                findings.append(
                    f"OS vm.swappiness={cur_val}. High swappiness evicts hot pages. Reduce to ≤10."
                )
        return findings

    # ── config snippet ────────────────────────────────────────────────────
    def _conf_snippet(self, wp, wc, rl, kt, cmb, pb) -> str:
        ssl_block = ""
        if self.inp.ssl_enabled:
            ssl_block = """
    ssl_protocols              TLSv1.2 TLSv1.3;
    ssl_ciphers                HIGH:!aNULL:!MD5;
    ssl_session_cache          shared:SSL:10m;
    ssl_session_timeout        10m;
    ssl_prefer_server_ciphers  on;
"""
        proxy_block = ""
        if self.inp.reverse_proxy:
            proxy_block = f"""
    proxy_buffer_size       {pb};
    proxy_buffers           4 {pb};
    proxy_busy_buffers_size {pb};
    proxy_connect_timeout   10s;
    proxy_send_timeout      30s;
    proxy_read_timeout      30s;
    proxy_http_version      1.1;
    proxy_set_header        Connection "";
"""
        return f"""# ── VAREX nginx.conf ({self.inp.mode.value.upper()} mode) ────────────────
worker_processes  {wp};
worker_rlimit_nofile {rl};

events {{
    worker_connections  {wc};
    use                 epoll;
    multi_accept        on;
}}

http {{
    sendfile             on;
    tcp_nopush           on;
    tcp_nodelay          on;
    keepalive_timeout    {kt};
    client_max_body_size {cmb};
    gzip                 on;
    gzip_vary            on;
    gzip_min_length      1024;
    open_file_cache      max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    server_tokens        off;
{ssl_block}{proxy_block}
    server {{
        listen  80;
        # listen 443 ssl http2;
        location / {{
            # add proxy_pass / root here
        }}
    }}
}}
"""

    def _ha_suggestions(self) -> list[str]:
        tips = [
            "Run ≥2 NGINX instances behind a cloud LB (round-robin or least_conn).",
            "Use shared-memory zones (limit_req_zone, limit_conn_zone) for cluster-wide rate-limiting.",
            "Store TLS session tickets in Redis for cross-instance SSL resumption.",
        ]
        if self.inp.reverse_proxy:
            tips.append("Add 'keepalive 32;' inside upstream{} to reuse backend connections.")
        return tips

    def _perf_warnings(self, wp, wc, mc) -> list[str]:
        warnings: list[str] = []
        if self.inp.expected_rps > mc:
            warnings.append(f"Expected RPS {self.inp.expected_rps} > max_clients {mc}. Add nodes.")
        if self.inp.cpu_cores == 1:
            warnings.append("Single core – consider multi-core for any production workload.")
        if self.inp.ram_gb < 2:
            warnings.append("< 2 GB RAM – worker memory severely constrained.")
        if not self.inp.ssl_enabled:
            warnings.append("SSL disabled – mandatory for internet-facing production traffic.")
        return warnings

    # ── public ───────────────────────────────────────────────────────────
    def generate(self) -> NginxOutput:
        wp  = self._worker_processes()
        wc  = self._worker_connections()
        rl  = self._rlimit()
        kt  = self._keepalive_timeout()
        cmb = self._client_max_body_size()
        pb  = self._proxy_buffer_size()
        mc  = self._max_clients(wp, wc)

        all_params = self._nginx_params(wp, wc, rl, kt, cmb, pb)

        # OS-level params via shared engine
        os_engine = OSTuningEngine(
            cpu_cores=self.inp.cpu_cores,
            ram_gb=self.inp.ram_gb,
            max_conns=mc,
            os_type=self.inp.os_type,
            existing_params=dict(self.inp.existing.os_sysctl) if self.inp.existing else {},
            disable_thp=False,
        )
        all_params += os_engine.generate()

        major  = [p for p in all_params if p.impact == ImpactLevel.MAJOR]
        medium = [p for p in all_params if p.impact == ImpactLevel.MEDIUM]
        minor  = [p for p in all_params if p.impact == ImpactLevel.MINOR]

        return NginxOutput(
            mode=self.inp.mode,
            worker_processes=wp, worker_connections=wc,
            worker_rlimit_nofile=rl, keepalive_timeout=kt,
            client_max_body_size=cmb, proxy_buffer_size=pb,
            recommended_ulimit=rl, estimated_max_clients=mc,
            capacity_warning=self._capacity_warning(self.inp.expected_rps, mc, "NGINX max_clients"),
            nginx_conf_snippet=self._conf_snippet(wp, wc, rl, kt, cmb, pb),
            major_params=major, medium_params=medium, minor_params=minor,
            os_sysctl_conf=os_engine.sysctl_conf_block(),
            ha_suggestions=self._ha_suggestions(),
            performance_warnings=self._perf_warnings(wp, wc, mc),
            audit_findings=self._audit(wp, wc, rl, kt) if self.inp.mode == CalcMode.EXISTING else [],
        )
