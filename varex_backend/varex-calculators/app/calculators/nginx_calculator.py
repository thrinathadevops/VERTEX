"""
app/calculators/nginx_calculator.py
====================================
NGINX tuning calculator — NEW and EXISTING modes.

Formulas used
-------------
worker_processes     = cpu_cores                     (1 worker per core)
worker_connections   = floor(RAM_per_worker_KB /
                             (16 + avg_response_kb + ssl_overhead_kb))
                       clamped to [512, 65535]
worker_rlimit_nofile = worker_connections * 2
estimated_max_clients= worker_processes * worker_connections
                       (÷4 for reverse_proxy — each proxied conn uses 4 FDs)
keepalive_timeout    = 65s (SSL) or 30s (plain),
                       reduced if expected_rps > 10000
client_max_body_size = 4 * avg_response_kb, capped at 100m
proxy_buffer_size    = next power-of-2 >= avg_response_kb, min 8k
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.nginx import NginxInput, NginxOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class NginxCalculator(BaseCalculator):

    _MEM_BASE_KB  = 16.0   # base memory per connection (kernel socket buffers)
    _SSL_EXTRA_KB = 64.0   # additional memory per SSL session (session cache + context)
    _MAX_WC       = 65535  # hard ceiling on worker_connections
    _PROXY_FD_MUL = 4      # each proxied connection uses 4 FDs

    def __init__(self, inp: NginxInput) -> None:
        self._require_positive(inp.cpu_cores,        "cpu_cores")
        self._require_positive(inp.ram_gb,           "ram_gb")
        self._require_positive(inp.expected_rps,     "expected_rps")
        self._require_positive(inp.avg_response_kb,  "avg_response_kb")
        self.inp = inp

    # ── internal calculations ─────────────────────────────────────────────────

    def _mem_per_conn_kb(self) -> float:
        """
        Memory cost per connection (KB).
        Base 16KB (kernel socket send/recv buffers) +
        avg_response_kb (response buffer held in memory) +
        64KB SSL overhead if ssl_enabled.
        """
        cost = self._MEM_BASE_KB + self.inp.avg_response_kb
        return cost + self._SSL_EXTRA_KB if self.inp.ssl_enabled else cost

    def _worker_processes(self) -> int:
        return self.inp.cpu_cores

    def _worker_connections(self) -> int:
        ram_per_worker_kb = (self.inp.ram_gb * 1024 * 1024) / self.inp.cpu_cores
        raw = math.floor(ram_per_worker_kb / self._mem_per_conn_kb())
        return max(512, min(raw, self._MAX_WC))

    def _worker_rlimit_nofile(self) -> int:
        return self._worker_connections() * 2

    def _keepalive_timeout(self) -> int:
        if not self.inp.keepalive_enabled:
            return 0
        base = 65 if self.inp.ssl_enabled else 30
        # Reduce under high RPS to free FDs faster
        return max(10, base - 20) if self.inp.expected_rps > 10_000 else base

    def _client_max_body_size(self) -> str:
        mb = max(1, min(int(self.inp.avg_response_kb * 4 / 1024), 100))
        return f"{mb}m"

    def _proxy_buffer_size(self) -> str:
        # Next power-of-2 >= avg_response_kb, minimum 8k
        kb = max(8, int(2 ** math.ceil(math.log2(max(1, self.inp.avg_response_kb)))))
        return f"{kb}k"

    def _estimated_max_clients(self, wp: int, wc: int) -> int:
        total = wp * wc
        return total // self._PROXY_FD_MUL if self.inp.reverse_proxy else total

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(
        self,
        wp:  int,
        wc:  int,
        rl:  int,
        kt:  int,
        cmb: str,
        pb:  str,
    ) -> list:
        ex  = self.inp.existing
        p   = self._p
        inp = self.inp

        ram_per_worker_kb = int(inp.ram_gb * 1024 * 1024 / inp.cpu_cores)
        mem_kb            = self._mem_per_conn_kb()

        params = [

            # ── MAJOR ────────────────────────────────────────────────────────
            p(
                "worker_processes", str(wp), M,
                f"Must equal vCPU count = {wp}. "
                "Each NGINX worker is single-threaded and pinned to one core. "
                "Under-provisioning: CPUs idle while requests queue. "
                "Over-provisioning: context-switch overhead degrades throughput. "
                "Use 'auto' in nginx.conf — NGINX reads /proc/cpuinfo at startup. "
                "Formula: 1 worker = 1 core.",
                f"worker_processes {wp};  # or: worker_processes auto;",
                str(ex.worker_processes) if ex.worker_processes else None,
            ),
            p(
                "worker_connections", str(wc), M,
                f"Max simultaneous connections per worker = {wc}. "
                f"Formula: RAM_per_worker ({ram_per_worker_kb:,} KB) / "
                f"mem_per_conn ({mem_kb:.0f} KB) = {wc}. "
                f"mem_per_conn = 16KB base + {inp.avg_response_kb}KB response"
                f"{' + 64KB SSL' if inp.ssl_enabled else ''}. "
                f"Total estimated_max_clients = {wp}×{wc}"
                f"{'÷4 (proxy FD cost)' if inp.reverse_proxy else ''} = "
                f"{self._estimated_max_clients(wp,wc):,}.",
                f"worker_connections {wc};",
                str(ex.worker_connections) if ex.worker_connections else None,
            ),
            p(
                "worker_rlimit_nofile", str(rl), M,
                f"Must be ≥ worker_connections × 2 = {rl}. "
                "Each proxied connection uses 2 FDs (client socket + upstream socket). "
                "Log file handles, cache file handles add more. "
                "If rlimit_nofile < worker_connections×2, NGINX silently rejects connections "
                "with EMFILE ('too many open files') in error.log. "
                "This value overrides the OS ulimit for the NGINX worker processes.",
                f"worker_rlimit_nofile {rl};",
                str(ex.worker_rlimit_nofile) if ex.worker_rlimit_nofile else None,
                safe=False,
            ),
            p(
                "use epoll + multi_accept", "epoll + on", M,
                "epoll is Linux O(1) event notification — scales to millions of FDs with "
                "constant CPU cost. select/poll are O(n): at 10K connections, each event "
                "scans 10K FDs. multi_accept: accept ALL new connections per epoll event "
                "instead of one-at-a-time, preventing accept queue buildup during bursts.",
                "events {
    use         epoll;
    multi_accept on;
}",
            ),
            p(
                "server_tokens", "off", M,
                "Default 'on' exposes NGINX version in Server header and error pages. "
                "Attackers use this for version-specific CVE targeting. "
                "Always off in production.",
                "server_tokens off;",
                ex.server_tokens,
            ),

            # ── MEDIUM ───────────────────────────────────────────────────────
            p(
                "client_header_buffer_size", "1k", MED,
                "Buffer for request line + headers. 1KB handles 95%+ of requests. "
                "If a request exceeds this, NGINX allocates from large_client_header_buffers "
                "(a slower path). Setting too large wastes memory for every connection.",
                "client_header_buffer_size 1k;",
                ex.client_header_buffer_size,
            ),
            p(
                "large_client_header_buffers", "4 16k", MED,
                "Fallback buffer pool for oversized headers. "
                "4 buffers × 16KB = 64KB maximum header size. "
                "Required for: JWT Authorization headers (2–8KB), "
                "large Cookie headers, SAML assertions in headers. "
                "Prevents 414 (URI Too Long) and 400 (Bad Request) errors on API gateways.",
                "large_client_header_buffers 4 16k;",
                ex.large_client_header_buffers,
            ),
            p(
                "client_body_buffer_size", "16k", MED,
                "Buffer for incoming request bodies. Bodies larger than 16KB spill to "
                "disk temp files (/tmp), adding disk I/O latency to every request. "
                "Increase to match your average POST/PUT payload size.",
                "client_body_buffer_size 16k;",
                ex.client_body_buffer_size,
            ),
            p(
                "client_max_body_size", cmb, MED,
                f"Hard upload size limit = {cmb}. "
                f"Formula: 4 × avg_response_size ({inp.avg_response_kb:.0f}KB), capped at 100MB. "
                "Too small → 413 (Request Entity Too Large) errors. "
                "Unlimited (0) → OOM risk from oversized uploads.",
                f"client_max_body_size {cmb};",
                ex.client_max_body_size,
            ),
            p(
                "client_body_timeout", "30s", MED,
                "Timeout for receiving the request body. Default 60s. "
                "Slow-loris attack: attacker sends request body at 1 byte/sec, holding "
                "a worker connection for 60s. At 1000 attackers: all workers blocked. "
                "30s limits exposure while allowing legitimate slow uploads.",
                "client_body_timeout 30s;",
                str(ex.client_body_timeout) if ex.client_body_timeout else None,
            ),
            p(
                "send_timeout", "30s", MED,
                "Timeout for sending response data to client. Default 60s. "
                "A dead or very slow client holds a worker connection open for 60s. "
                "Under high load: 30s frees the FD 2× faster.",
                "send_timeout 30s;",
                str(ex.send_timeout) if ex.send_timeout else None,
            ),
            p(
                "keepalive_timeout", str(kt), MED,
                f"Idle keep-alive connection timeout = {kt}s. "
                f"Base: {'65s (SSL — avoids TLS re-handshake)' if inp.ssl_enabled else '30s (plain HTTP)'}. "
                f"{'Reduced by 20s because expected_rps=' + str(inp.expected_rps) + ' > 10K.' if inp.expected_rps > 10000 else ''} "
                "Tradeoff: higher = fewer TCP+TLS handshakes; lower = fewer idle FD holders. "
                "At 10K idle keep-alives × 30s = 300K FD-seconds consumed.",
                f"keepalive_timeout {kt};",
                str(ex.keepalive_timeout) if ex.keepalive_timeout else None,
            ),
            p(
                "reset_timedout_connection", "on", MED,
                "Send TCP RST on timeout instead of waiting for the full FIN→FIN-ACK sequence. "
                "RST frees the FD immediately. FIN sequence adds up to 60s TIME_WAIT. "
                "Critical under high concurrency where FD exhaustion is the bottleneck.",
                "reset_timedout_connection on;",
                ex.reset_timedout_connection,
            ),
            p(
                "sendfile + tcp_nopush + tcp_nodelay", "on", MED,
                "sendfile(): zero-copy transfer from disk → socket via kernel, bypassing "
                "userspace. Without it: read() to userspace buffer → write() to socket = "
                "2 memory copies. tcp_nopush: batch small TCP segments to reduce header "
                "overhead (enable with sendfile). tcp_nodelay: disable Nagle's algorithm "
                "for low-latency streaming. "
                "Together: 30–50% throughput improvement for static file serving.",
                "sendfile    on;
tcp_nopush  on;
tcp_nodelay on;",
            ),
            p(
                "open_file_cache", "max=200000 inactive=20s", MED,
                "Cache open file descriptors, stat() results, and directory lookups. "
                "Without this, each static file request calls: open() + fstat() + close() "
                "= 3 syscalls. With 200K cached entries, these become memory lookups. "
                f"200K entries covers large static sites. inactive=20s evicts cold entries. "
                f"Sized for {inp.static_pct:.0f}% static workload.",
                "open_file_cache          max=200000 inactive=20s;
"
                "open_file_cache_valid    30s;
"
                "open_file_cache_min_uses 2;
"
                "open_file_cache_errors   on;",
            ),
            p(
                "gzip compression", "on", MED,
                "GZIP reduces text/JSON/HTML payload size by 60–80%. "
                "CPU cost: <1% on modern hardware for typical API payloads. "
                "gzip_vary: adds 'Vary: Accept-Encoding' header — required for correct "
                "behaviour behind CDNs and proxy caches. "
                "gzip_min_length 1024: don't compress small responses (compression overhead "
                "exceeds savings for payloads < 1KB).",
                "gzip            on;
"
                "gzip_vary       on;
"
                "gzip_min_length 1024;
"
                "gzip_comp_level 4;
"
                "gzip_types      text/plain text/css application/json "
                "application/javascript text/xml application/xml;",
                ex.gzip,
            ),
        ]

        # ── SSL params (only when ssl_enabled) ───────────────────────────────
        if inp.ssl_enabled:
            params += [
                p(
                    "ssl_protocols", "TLSv1.2 TLSv1.3", MED,
                    "Disable TLSv1.0 (POODLE, CVE-2014-3566) and TLSv1.1 (BEAST). "
                    "TLSv1.3: 1-RTT handshake vs 2-RTT for TLSv1.2 — saves ~50ms per "
                    "new connection. PCI-DSS 3.2.1 mandates removal of TLS < 1.2.",
                    "ssl_protocols TLSv1.2 TLSv1.3;",
                    ex.ssl_protocols,
                ),
                p(
                    "ssl_session_cache", "shared:SSL:50m", MED,
                    "Shared TLS session cache across ALL worker processes. "
                    "50MB ≈ 200,000 sessions. Without shared cache, each worker has its own "
                    "cache — a client reconnecting to a different worker gets a full handshake. "
                    "Session resumption eliminates the 2-RTT handshake saving ~100ms/connection.",
                    "ssl_session_cache   shared:SSL:50m;
"
                    "ssl_session_timeout 600s;
"
                    "ssl_session_tickets off;  # tickets have forward-secrecy implications",
                ),
                p(
                    "ssl_buffer_size", "4k", MED,
                    "Default 16KB. NGINX sends TLS records in 16KB chunks, "
                    "which fragments typical API responses (1–4KB) into multiple TCP segments. "
                    "4KB aligns TLS record size to standard Ethernet MTU (1500 bytes) "
                    "reducing TCP segment count and improving TTFB (time-to-first-byte). "
                    "Use 16k only for large static file streaming.",
                    "ssl_buffer_size 4k;",
                    ex.ssl_buffer_size,
                ),
                p(
                    "ssl_stapling", "on", MIN,
                    "OCSP stapling: NGINX fetches and caches the certificate revocation "
                    "status, stapling it to the TLS handshake. Without stapling, browsers "
                    "must fetch OCSP themselves adding 50–200ms to every new TLS connection.",
                    "ssl_stapling            on;
"
                    "ssl_stapling_verify     on;
"
                    "ssl_prefer_server_ciphers on;
"
                    "ssl_ciphers             ECDHE-ECDSA-AES128-GCM-SHA256:"
                    "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:"
                    "ECDHE-RSA-AES256-GCM-SHA384;",
                ),
            ]

        # ── Reverse proxy params ──────────────────────────────────────────────
        if inp.reverse_proxy:
            params += [
                p(
                    "proxy_buffer_size", pb, MED,
                    f"Buffer for upstream response headers = {pb}. "
                    "Must hold the complete response header from the backend. "
                    "If header > buffer, NGINX falls through to disk buffering, "
                    "adding latency and I/O. "
                    f"Formula: next power-of-2 ≥ avg_response_kb ({inp.avg_response_kb}KB).",
                    f"proxy_buffer_size      {pb};
"
                    f"proxy_buffers          4 {pb};
"
                    f"proxy_busy_buffers_size {pb};",
                ),
                p(
                    "proxy_connect_timeout", "10s", MED,
                    "Fail fast on dead upstreams = 10s. Default 60s means each dead backend "
                    "holds a worker thread for 60s. At 100 dead-backend attempts: all workers "
                    "blocked for 60s. 10s = circuit-break in 10s.",
                    "proxy_connect_timeout  10s;
"
                    "proxy_send_timeout     30s;
"
                    "proxy_read_timeout     30s;",
                ),
                p(
                    "upstream keepalive", "32", MED,
                    "Idle keepalive connections per worker to upstream backends. "
                    "Without keepalive: every proxied request opens a new TCP connection "
                    "to upstream — at 10K RPS: 10K TCP handshakes/sec to backend. "
                    "Formula: upstream_maxThreads / nginx_worker_count. "
                    "Requires proxy_http_version 1.1 and Connection '' header.",
                    "upstream backend {
"
                    "    server 127.0.0.1:8080;
"
                    "    keepalive 32;
"
                    "}",
                ),
                p(
                    "proxy_http_version 1.1", "1.1", MED,
                    "HTTP/1.1 is required for upstream keepalive connections. "
                    "HTTP/1.0 (default) closes the connection after each request, "
                    "negating the keepalive benefit. "
                    "Connection '' clears the 'Connection: close' header from clients.",
                    'proxy_http_version              1.1;
'
                    'proxy_set_header Connection     "";
'
                    'proxy_set_header Host           $host;
'
                    'proxy_set_header X-Real-IP      $remote_addr;
'
                    'proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
'
                    'proxy_set_header X-Forwarded-Proto $scheme;',
                ),
            ]

        # ── MINOR ────────────────────────────────────────────────────────────
        params += [
            p(
                "access_log buffering", "buffer=512k flush=5s", MIN,
                "Without buffering, every request triggers a write() syscall. "
                "At 10K RPS: 10,000 write() calls/sec → significant I/O overhead. "
                "512KB buffer flushes every 5s = ~1 write/5 seconds, "
                "reducing log I/O by 99.99%.",
                "access_log /var/log/nginx/access.log main buffer=512k flush=5s;",
            ),
            p(
                "error_log level", "warn", MIN,
                "debug/info modes generate logs for every connection event. "
                "At 10K RPS with debug: GB/hour of logs. 'warn' logs only actionable issues.",
                "error_log /var/log/nginx/error.log warn;",
            ),
            p(
                "worker_cpu_affinity", "auto", MIN,
                "Bind workers to specific CPU cores to improve L1/L2 cache hit rate. "
                "'auto' lets NGINX detect and bind automatically. "
                "Reduces CPU cache thrashing on NUMA systems.",
                "worker_cpu_affinity auto;",
            ),
            p(
                "worker_priority", "0", MIN,
                "Nice priority for worker processes. 0 = normal. "
                "Lower values (-5 to -20) give NGINX higher CPU scheduling priority "
                "over background tasks. Use -5 for latency-sensitive deployments.",
                "worker_priority 0;",
            ),
            p(
                "keepalive_requests", "1000", MIN,
                "Max requests per keep-alive connection before forcing reconnection. "
                "Default 1000 is reasonable. Increase for long-lived browser sessions.",
                "keepalive_requests 1000;",
            ),
        ]

        return params

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, wp: int, wc: int, rl: int, kt: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.worker_processes and ex.worker_processes != wp:
            direction = "Under-utilising CPUs." if ex.worker_processes < wp else "Excess context-switch overhead."
            findings.append(
                f"[MAJOR] worker_processes={ex.worker_processes}, recommended={wp}. {direction}"
            )
        if ex.worker_connections and ex.worker_connections < wc * 0.5:
            findings.append(
                f"[MAJOR] worker_connections={ex.worker_connections} is < 50% of "
                f"recommended {wc}. Severe concurrency bottleneck."
            )
        if ex.worker_rlimit_nofile and ex.worker_rlimit_nofile < wc * 2:
            findings.append(
                f"[MAJOR] worker_rlimit_nofile={ex.worker_rlimit_nofile} < "
                f"worker_connections×2={wc*2}. Will hit EMFILE 'too many open files' errors."
            )
        if ex.ssl_protocols:
            for weak in ("TLSv1 ", "TLSv1.1", "SSLv3", "SSLv2"):
                if weak in ex.ssl_protocols:
                    findings.append(
                        f"[MAJOR] ssl_protocols contains {weak.strip()} — deprecated, "
                        "CVE-vulnerable (POODLE/BEAST). Remove immediately."
                    )
        if ex.ssl_buffer_size == "16k":
            findings.append(
                "[MEDIUM] ssl_buffer_size=16k fragments API responses into multiple TCP segments. "
                "Reduce to 4k to improve TTFB."
            )
        if ex.server_tokens and ex.server_tokens.lower() == "on":
            findings.append(
                "[MEDIUM] server_tokens=on exposes NGINX version in headers and error pages. "
                "Set to off."
            )
        if ex.keepalive_timeout and ex.keepalive_timeout > 120:
            findings.append(
                f"[MEDIUM] keepalive_timeout={ex.keepalive_timeout}s. "
                f"Idle FD consumption = RPS × timeout. Reduce to {kt}s."
            )
        for k, v in ex.os_sysctl.items():
            try:
                if k == "net.core.somaxconn" and int(v) < 1024:
                    findings.append(
                        f"[MAJOR] OS net.core.somaxconn={v} (Linux default=128). "
                        "Silent SYN packet drops under any real load."
                    )
                if k == "vm.swappiness" and int(v) > 30:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. Hot pages being swapped, "
                        "causing latency spikes. Reduce to 10."
                    )
                if k == "fs.file-max":
                    fd = self._worker_rlimit_nofile() * self.inp.cpu_cores
                    if int(v) < fd:
                        findings.append(
                            f"[MAJOR] fs.file-max={v} < required {fd}. "
                            "OS-level FD exhaustion risk."
                        )
            except ValueError:
                pass  # non-numeric sysctl value

        return findings

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self, wp: int, wc: int, rl: int, kt: int, cmb: str, pb: str) -> str:
        inp = self.inp

        ssl_block = ""
        if inp.ssl_enabled:
            ssl_block = (
                "
    # ── SSL ──────────────────────────────────────────────
"
                "    ssl_protocols              TLSv1.2 TLSv1.3;
"
                "    ssl_ciphers                ECDHE-ECDSA-AES128-GCM-SHA256:"
                "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
"
                "    ssl_prefer_server_ciphers  on;
"
                "    ssl_session_cache          shared:SSL:50m;
"
                "    ssl_session_timeout        600s;
"
                "    ssl_session_tickets        off;
"
                "    ssl_buffer_size            4k;
"
                "    ssl_stapling               on;
"
                "    ssl_stapling_verify        on;
"
            )

        proxy_block = ""
        if inp.reverse_proxy:
            proxy_block = (
                "
    # ── Proxy ────────────────────────────────────────────
"
                f"    proxy_buffer_size          {pb};
"
                f"    proxy_buffers              4 {pb};
"
                f"    proxy_busy_buffers_size    {pb};
"
                "    proxy_connect_timeout      10s;
"
                "    proxy_send_timeout         30s;
"
                "    proxy_read_timeout         30s;
"
                "    proxy_http_version         1.1;
"
                '    proxy_set_header Connection     "";
'
                '    proxy_set_header Host           $host;
'
                '    proxy_set_header X-Real-IP      $remote_addr;
'
                '    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
'
                '    proxy_set_header X-Forwarded-Proto $scheme;
'
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX NGINX Config  [{inp.mode.value.upper():8s}]  "
            f"cores={wp}  RAM={inp.ram_gb}GB           ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"worker_processes      {wp};   # auto also works
"
            f"worker_rlimit_nofile  {rl};
"
            f"worker_priority       0;
"
            f"worker_cpu_affinity   auto;

"
            f"events {{
"
            f"    worker_connections  {wc};
"
            f"    use                 epoll;
"
            f"    multi_accept        on;
"
            f"}}

"
            f"http {{
"
            f"    # ── Core ─────────────────────────────────────────────
"
            f"    sendfile              on;
"
            f"    tcp_nopush            on;
"
            f"    tcp_nodelay           on;
"
            f"    server_tokens         off;
"
            f"    keepalive_timeout     {kt};
"
            f"    keepalive_requests    1000;

"
            f"    # ── Buffers / Timeouts ───────────────────────────────
"
            f"    client_header_buffer_size   1k;
"
            f"    large_client_header_buffers 4 16k;
"
            f"    client_body_buffer_size     16k;
"
            f"    client_max_body_size        {cmb};
"
            f"    client_body_timeout         30s;
"
            f"    send_timeout                30s;
"
            f"    reset_timedout_connection   on;

"
            f"    # ── File cache ───────────────────────────────────────
"
            f"    open_file_cache          max=200000 inactive=20s;
"
            f"    open_file_cache_valid    30s;
"
            f"    open_file_cache_min_uses 2;
"
            f"    open_file_cache_errors   on;

"
            f"    # ── Compression ──────────────────────────────────────
"
            f"    gzip            on;
"
            f"    gzip_vary       on;
"
            f"    gzip_min_length 1024;
"
            f"    gzip_comp_level 4;
"
            f"    gzip_types      text/plain text/css application/json "
            f"application/javascript text/xml application/xml;
"
            f"{ssl_block}"
            f"{proxy_block}
"
            f"    # ── Logging ──────────────────────────────────────────
"
            f"    access_log  /var/log/nginx/access.log main buffer=512k flush=5s;
"
            f"    error_log   /var/log/nginx/error.log warn;

"
            f"    server {{
"
            f"        listen       80;
"
            f"        # listen     443 ssl http2;   # uncomment for HTTPS
"
            f"        server_name  _;
"
            f"        # location / {{ ... }}
"
            f"    }}
"
            f"}}
"
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> NginxOutput:
        wp  = self._worker_processes()
        wc  = self._worker_connections()
        rl  = self._worker_rlimit_nofile()
        kt  = self._keepalive_timeout()
        cmb = self._client_max_body_size()
        pb  = self._proxy_buffer_size()
        mc  = self._estimated_max_clients(wp, wc)

        # Build NGINX-specific params
        all_params = self._build_params(wp, wc, rl, kt, cmb, pb)

        # Append shared OS/kernel params
        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = mc,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        return NginxOutput(
            mode                  = self.inp.mode,
            worker_processes      = wp,
            worker_connections    = wc,
            worker_rlimit_nofile  = rl,
            keepalive_timeout     = kt,
            client_max_body_size  = cmb,
            proxy_buffer_size     = pb,
            estimated_max_clients = mc,
            nginx_conf_snippet    = self._render_conf(wp, wc, rl, kt, cmb, pb),
            major_params          = major,
            medium_params         = medium,
            minor_params          = minor,
            os_sysctl_conf        = os_engine.sysctl_block(),
            ha_suggestions=[
                "Deploy 2+ NGINX nodes behind a cloud LB (AWS ALB/NLB) with least_conn algorithm.",
                "Store TLS session tickets in a shared Redis backend for cross-node SSL resumption.",
                "Use shared limit_req_zone backed by Redis for cluster-wide rate limiting.",
                "Configure upstream max_fails=2 fail_timeout=10s for fast circuit-breaking.",
                "Use NGINX Plus or OpenResty for active upstream health checks.",
                "Enable NGINX stub_status + Prometheus NGINX Exporter for worker/connection dashboards.",
            ],
            performance_warnings=[w for w in [
                (f"Expected RPS {self.inp.expected_rps:,} > estimated max_clients {mc:,}. "
                 "Add more nodes or increase RAM.")
                if self.inp.expected_rps > mc else None,
                "Single CPU core — multi-core is mandatory for production workloads."
                if self.inp.cpu_cores == 1 else None,
                "RAM < 2GB — severely constrained for a production NGINX instance."
                if self.inp.ram_gb < 2 else None,
                "SSL disabled — HTTPS is mandatory for production. Enable TLS termination."
                if not self.inp.ssl_enabled else None,
            ] if w],
            capacity_warning = self._capacity_warning(
                self.inp.expected_rps, mc, "NGINX estimated_max_clients"
            ),
            audit_findings = self._audit(wp, wc, rl, kt)
                             if self.inp.mode == CalcMode.EXISTING else [],
        )
