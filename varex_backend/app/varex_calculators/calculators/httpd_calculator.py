"""
app/calculators/httpd_calculator.py
=====================================
Apache HTTPD tuning calculator — NEW and EXISTING modes.

MaxRequestWorkers formula
-------------------------
event / worker MPM:
  mrw = min(cpu_cores × 2 × ThreadsPerChild, 16384)
  clamped to max(expected_concurrent, mrw)

prefork MPM:
  mrw = min(floor(RAM_GB × 1024 × 0.70 / MEM_PER_PROC_MB), 1024)
  Where MEM_PER_PROC_MB = 10.0 (typical Apache prefork process, no mod_php)
  With mod_php: 30–60MB per process — user should adjust.

ServerLimit formula
-------------------
event/worker: ceil(MaxRequestWorkers / ThreadsPerChild) + 4
prefork:      MaxRequestWorkers  (1 process = 1 server)

ThreadsPerChild
---------------
event/worker: 25 (Apache default, empirically balanced)
prefork:      1  (prefork is single-threaded per process)

SendBufferSize / ReceiveBufferSize
----------------------------------
5% of RAM in bytes, capped at 256MB
"""
from __future__ import annotations

import math

from app.varex_calculators.calculators.base import BaseCalculator
from app.varex_calculators.calculators.os_tuning import OSTuningEngine
from app.varex_calculators.core.enums import ImpactLevel, CalcMode
from app.varex_calculators.schemas.httpd import HttpdInput, HttpdOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR

_MEM_PREFORK_MB = 10.0   # MB per prefork process (no mod_php; with mod_php use 30–60)


class HttpdCalculator(BaseCalculator):

    def __init__(self, inp: HttpdInput) -> None:
        self._require_positive(inp.cpu_cores,            "cpu_cores")
        self._require_positive(inp.ram_gb,               "ram_gb")
        self._require_positive(inp.expected_concurrent,  "expected_concurrent")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _tpc(self) -> int:
        """ThreadsPerChild: 1 for prefork (single-threaded), 25 for event/worker."""
        return 1 if self.inp.mpm == "prefork" else 25

    def _mrw(self) -> int:
        """
        MaxRequestWorkers / MaxClients.

        prefork: limited by RAM — each process costs ~10MB baseline.
          Formula: min(floor(RAM × 1024 × 0.70 / 10), 1024)
          70% RAM to Apache, 30% to OS + other processes.
          Hard cap 1024: prefork doesn't scale beyond ~1024 processes.

        event/worker: limited by threads.
          Formula: max(expected_concurrent, cpu_cores × 2 × TPC)
          cpu_cores × 2: hyperthreading headroom.
          × TPC: threads per child process.
          Capped at 16384 (hard Apache limit).
        """
        if self.inp.mpm == "prefork":
            ram_budget_mb = self.inp.ram_gb * 1024 * 0.70
            raw = math.floor(ram_budget_mb / _MEM_PREFORK_MB)
            return max(self.inp.expected_concurrent, min(raw, 1024))
        else:
            thread_based = self.inp.cpu_cores * 2 * self._tpc()
            return min(max(self.inp.expected_concurrent, thread_based), 16_384)

    def _sl(self, mrw: int) -> int:
        """
        ServerLimit.
        event/worker: ceil(MRW / TPC) + 4  (extra 4 for graceful restart headroom)
        prefork:      = MRW  (1 process per connection)
        CRITICAL: ServerLimit must be set BEFORE MaxRequestWorkers in httpd.conf.
        If ServerLimit < ceil(MRW/TPC), MaxRequestWorkers is silently capped.
        """
        if self.inp.mpm == "prefork":
            return mrw
        return math.ceil(mrw / self._tpc()) + 4

    def _mst(self, mrw: int) -> int:
        """MinSpareThreads: max(10, MRW // 10)"""
        return max(10, mrw // 10)

    def _mxst(self, mrw: int) -> int:
        """MaxSpareThreads: max(75, MRW // 4)"""
        return max(75, mrw // 4)

    def _buf(self) -> int:
        """TCP send/recv buffer: 5% RAM, capped at 256MB."""
        return min(int(self.inp.ram_gb * 1024 * 1024 * 1024 * 0.05), 268_435_456)

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        buf  = self._buf()

        params = [

            # ── MAJOR: MPM / concurrency / security ───────────────────────
            p(
                "MPM selection", inp.mpm, M,
                {
                    "event": (
                        "Event MPM (default Apache 2.4+): single dedicated listener thread "
                        "handles all keep-alive connections — frees worker threads between requests. "
                        "Handles C10K (10,000 simultaneous connections) efficiently. "
                        "Best for: modern web apps, APIs, reverse proxy, SSL. "
                        "Requires thread-safe modules (no mod_php)."
                    ),
                    "worker": (
                        "Worker MPM: thread-per-connection model. "
                        "Better than prefork (shared memory between threads) but "
                        "keep-alive connections hold a full thread (unlike event). "
                        "Good for: moderate concurrency, mixed static/dynamic. "
                        "Requires thread-safe modules."
                    ),
                    "prefork": (
                        "Prefork MPM: one process per connection, no threads. "
                        "Required for: mod_php (not thread-safe), legacy C extensions. "
                        f"RAM cost: {_MEM_PREFORK_MB}MB per process baseline. "
                        f"At {inp.ram_gb}GB × 70% / {_MEM_PREFORK_MB}MB = "
                        f"{int(inp.ram_gb*1024*0.70/_MEM_PREFORK_MB)} max processes. "
                        "Hard ceiling: 1024. NEVER use for > 1024 concurrent connections."
                    ),
                }.get(inp.mpm, ""),
                f"LoadModule mpm_{inp.mpm}_module modules/mod_mpm_{inp.mpm}.so",
                ex.mpm_model,
                safe=False,
            ),
            p(
                "MaxRequestWorkers", str(mrw), M,
                f"Maximum simultaneous connections = {mrw}. "
                + (
                    f"prefork formula: floor(RAM×1024×0.70 / {_MEM_PREFORK_MB}MB) = {mrw}. "
                    f"With mod_php: use 30–60MB/process → max {int(inp.ram_gb*1024*0.70/40)} workers. "
                    "Hitting MaxRequestWorkers: Apache returns 503 immediately."
                    if inp.mpm == "prefork" else
                    f"event/worker formula: max(expected_concurrent={inp.expected_concurrent}, "
                    f"cpu_cores×2×TPC={inp.cpu_cores}×2×{tpc}) = {mrw}. "
                    "Hitting MaxRequestWorkers: Apache returns 503 immediately."
                ),
                f"MaxRequestWorkers {mrw}",
                str(ex.max_request_workers) if ex.max_request_workers else None,
                safe=False,
            ),
            p(
                "ServerLimit", str(sl), M,
                f"Max number of child processes = {sl}. "
                + (
                    f"Formula: ceil(MRW/TPC) + 4 = ceil({mrw}/{tpc}) + 4 = {sl}. "
                    "CRITICAL: ServerLimit MUST be set BEFORE MaxRequestWorkers in httpd.conf. "
                    "If ServerLimit is too low, Apache silently truncates MaxRequestWorkers "
                    "at startup with no error message. "
                    "Requires full Apache restart (not graceful reload) to take effect."
                    if inp.mpm != "prefork" else
                    f"prefork: ServerLimit = MaxRequestWorkers = {sl}. "
                    "Changing ServerLimit requires full restart."
                ),
                f"ServerLimit {sl}",
                str(ex.server_limit) if ex.server_limit else None,
                safe=False,
            ),
            p(
                "ThreadsPerChild", str(tpc), M,
                f"Worker threads per child process = {tpc}. "
                + (
                    "prefork: always 1 (single-threaded per process by design)."
                    if inp.mpm == "prefork" else
                    f"event/worker: {tpc} threads per child (Apache default). "
                    "Total thread capacity = ServerLimit × ThreadsPerChild = "
                    f"{sl} × {tpc} = {sl * tpc}. "
                    "Must satisfy: ServerLimit × ThreadsPerChild ≥ MaxRequestWorkers. "
                    "If not: MaxRequestWorkers silently capped at ServerLimit × ThreadsPerChild."
                ),
                f"ThreadsPerChild {tpc}",
                str(ex.threads_per_child) if ex.threads_per_child else None,
                safe=False,
            ),
            p(
                "ServerTokens", "Prod", M,
                "Default 'Full' exposes: Apache/2.4.58 (Ubuntu) in Server header. "
                "Attackers use this to target specific Apache CVEs. "
                "'Prod' outputs only 'Apache' — minimal version disclosure. "
                "Combined with ServerSignature Off and TraceEnable Off: "
                "removes version from error pages and disables HTTP TRACE method "
                "(used in Cross-Site Tracing / XST attacks).",
                "ServerTokens Prod
ServerSignature Off
TraceEnable Off",
                ex.server_tokens,
            ),

            # ── MEDIUM: connection / buffer tuning ────────────────────────
            p(
                "MinSpareThreads", str(mst), MED,
                f"Pre-warmed idle threads = {mst} (= MaxRequestWorkers ÷ 10). "
                "When traffic spikes, Apache spawns new threads to meet demand. "
                "Thread creation costs 5–20ms and CPU. MinSpareThreads = "
                "immediate response capacity for traffic bursts.",
                f"MinSpareThreads {mst}",
                str(ex.min_spare_threads) if ex.min_spare_threads else None,
            ),
            p(
                "MaxSpareThreads", str(mxst), MED,
                f"Max idle threads before Apache starts killing them = {mxst} "
                f"(= MaxRequestWorkers ÷ 4). "
                "Too high: wasted RAM on idle threads during off-peak. "
                "Too low: threads are destroyed and re-created on every traffic wave.",
                f"MaxSpareThreads {mxst}",
                str(ex.max_spare_threads) if ex.max_spare_threads else None,
            ),
            p(
                "KeepAlive", "On", MED,
                "HTTP persistent connections. Without KeepAlive, every request "
                "requires a new TCP handshake + (with SSL) TLS handshake. "
                "TLS 1.2 handshake = 2 RTT ≈ 50–100ms overhead per request. "
                "KeepAlive eliminates this for all subsequent requests on the same connection.",
                "KeepAlive On",
                ex.keep_alive,
            ),
            p(
                "KeepAliveTimeout", "15", MED,
                "Default 5s is too short for AJAX-heavy apps making multiple parallel API calls. "
                "15s: client reuses connection for subsequent requests within 15s. "
                "Reduce to 5s for high-RPS stateless APIs where connections turn over rapidly.",
                "KeepAliveTimeout 15",
                str(ex.keep_alive_timeout) if ex.keep_alive_timeout else None,
            ),
            p(
                "MaxKeepAliveRequests", "500", MED,
                "Default 100 forces re-connection every 100 requests. "
                "500: long-lived browser sessions with many assets avoid repeated TCP setup. "
                "Set to 0 for unlimited (only on trusted internal networks).",
                "MaxKeepAliveRequests 500",
                str(ex.max_keep_alive_requests) if ex.max_keep_alive_requests else None,
            ),
            p(
                "Timeout", "30", MED,
                "Default 300s holds Apache workers for 5 minutes on slow/dead clients. "
                "At maxRequestWorkers={mrw}: 300s timeout × slow clients = "
                "rapid worker exhaustion under any traffic anomaly. "
                "30s: workers freed 10× faster. Increase only for large upload endpoints.",
                "Timeout 30",
                str(ex.timeout) if ex.timeout else None,
            ),
            p(
                "LimitRequestLine", "16384", MED,
                "Default 8KB. REST APIs with long query strings, "
                "JWT tokens in URL, or deeply nested paths need 16KB. "
                "Clients exceeding this receive 414 Request-URI Too Long. "
                "Set to 8192 for strict security; 16384 for API gateways.",
                "LimitRequestLine 16384",
                str(ex.limit_request_line) if ex.limit_request_line else None,
            ),
            p(
                "LimitRequestFieldSize", "16384", MED,
                "Per-header value size limit. Default 8KB. "
                "Large Authorization headers (JWT Bearer = 1–8KB), "
                "Cookie headers (session + tracking = up to 8KB), "
                "SAML assertions (up to 16KB) all require ≥ 16KB.",
                "LimitRequestFieldSize 16384",
                str(ex.limit_request_field_size) if ex.limit_request_field_size else None,
            ),
            p(
                "LimitRequestBody", "1073741824", MED,
                "1GB upload limit (default: 0 = unlimited). "
                "Unlimited body size risks OOM from a single oversized request. "
                "1GB is generous for file upload APIs. "
                "Reduce to 10485760 (10MB) for JSON API-only endpoints.",
                "LimitRequestBody 1073741824",
                str(ex.limit_request_body) if ex.limit_request_body else None,
            ),
            p(
                "SendBufferSize", str(buf), MED,
                f"TCP send buffer = 5% RAM = {buf:,} bytes. "
                "Larger buffers improve large file and video streaming throughput "
                "by reducing the number of write() syscalls needed per response.",
                f"SendBufferSize {buf}",
                str(ex.send_buffer_size) if ex.send_buffer_size else None,
            ),
            p(
                "ReceiveBufferSize", str(buf), MED,
                f"TCP receive buffer = {buf:,} bytes (mirrors SendBufferSize). "
                "Improves upload throughput and reduces retransmission events.",
                f"ReceiveBufferSize {buf}",
                str(ex.receive_buffer_size) if ex.receive_buffer_size else None,
            ),
            p(
                "MaxConnectionsPerChild", "10000", MED,
                "Recycle child processes after handling 10,000 connections. "
                "Prevents long-lived processes from growing indefinitely due to "
                "memory fragmentation and slow memory leaks in C modules. "
                "0 = never recycle (default — allows unbounded memory growth).",
                "MaxConnectionsPerChild 10000",
                str(ex.max_connections_per_child) if ex.max_connections_per_child else None,
            ),
        ]

        # ── SSL params ────────────────────────────────────────────────────
        if inp.ssl_enabled:
            params += [
                p(
                    "SSLProtocol", "TLSv1.2 TLSv1.3", MED,
                    "Disable TLSv1.0 (POODLE, CVE-2014-3566) and TLSv1.1 (BEAST). "
                    "TLSv1.3: 1-RTT handshake — saves ~50ms per new connection vs TLSv1.2 (2-RTT). "
                    "PCI-DSS 3.2.1 mandates removal of TLS < 1.2.",
                    "SSLProtocol -all +TLSv1.2 +TLSv1.3",
                ),
                p(
                    "SSLSessionCache", "shmcb:/run/apache2/ssl_scache(512000)", MED,
                    "Shared TLS session cache across ALL child processes. "
                    "512KB ≈ 4,000 sessions. Without shared cache: "
                    "a client reconnecting to a different child process gets a full 2-RTT handshake. "
                    "Session resumption eliminates the TLS handshake entirely.",
                    "SSLSessionCache shmcb:/run/apache2/ssl_scache(512000)
"
                    "SSLSessionCacheTimeout 600",
                ),
                p(
                    "SSLCipherSuite", "ECDHE+AESGCM:ECDHE+CHACHA20", MED,
                    "Forward-secret cipher suites only. "
                    "ECDHE: ephemeral key exchange — past traffic cannot be decrypted "
                    "even if private key is later compromised. "
                    "AESGCM: authenticated encryption (AEAD), hardware-accelerated on modern CPUs. "
                    "ChaCha20: better performance on devices without AES hardware (mobile).",
                    "SSLCipherSuite ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!MD5:!DSS
"
                    "SSLHonorCipherOrder on
"
                    "SSLCompression off
"
                    "SSLUseStapling on
"
                    "SSLStaplingCache shmcb:/run/apache2/stapling_cache(131072)",
                ),
            ]

        # ── reverse proxy params ──────────────────────────────────────────
        if inp.reverse_proxy:
            params += [
                p(
                    "mod_proxy keepalive", "On", MED,
                    "Backend keepalive: reuse backend connections across requests. "
                    "Without: every proxied request opens a new TCP connection to backend. "
                    "At 5000 RPS: 5000 TCP handshakes/sec to backend = backend CPU spike. "
                    "enablereuse=on requires mod_proxy_http + SetEnv proxy-nokeepalive 0.",
                    "ProxyPass / http://backend:8080/ enablereuse=on
"
                    "ProxyPassReverse / http://backend:8080/
"
                    "ProxyTimeout 30
"
                    "ProxyBadHeader Ignore",
                ),
                p(
                    "mod_proxy balancer", "byrequests", MED,
                    "Load-balance across multiple backends with round-robin by default. "
                    "byrequests: equal distribution (default). "
                    "bybusyness: route to least-busy worker (better for variable response times). "
                    "Requires mod_proxy_balancer + mod_status for monitoring.",
                    "<Proxy balancer://mycluster>
"
                    "    BalancerMember http://backend1:8080
"
                    "    BalancerMember http://backend2:8080
"
                    "    ProxySet lbmethod=bybusyness
"
                    "</Proxy>
"
                    "ProxyPass        / balancer://mycluster/
"
                    "ProxyPassReverse / balancer://mycluster/",
                ),
            ]

        # ── static file params ────────────────────────────────────────────
        if inp.serve_static:
            params += [
                p(
                    "EnableSendfile + EnableMMAP", "On", MED,
                    "EnableSendfile: zero-copy transfer from disk → socket via sendfile() syscall. "
                    "Bypasses userspace: no read() → write() memory copy. "
                    "EnableMMAP: memory-mapped file reads for static content. "
                    "Together: 30–50% throughput improvement for static file serving. "
                    "Disable if files are on NFS (sendfile unreliable over network filesystems).",
                    "EnableSendfile on
EnableMMAP on",
                ),
                p(
                    "mod_deflate / mod_brotli", "enabled", MED,
                    "GZIP (mod_deflate) or Brotli (mod_brotli) compression. "
                    "Reduces HTML/CSS/JS/JSON payload by 60–80%. "
                    "Brotli: 20–26% better compression than GZIP at same CPU cost (Apache 2.4.26+). "
                    "AddOutputFilterByType: only compress text types, never compress already-compressed "
                    "formats (JPEG, PNG, MP4) — waste of CPU with size increase.",
                    "LoadModule deflate_module modules/mod_deflate.so
"
                    "AddOutputFilterByType DEFLATE text/html text/css text/plain "
                    "application/json application/javascript text/xml application/xml",
                ),
            ]

        # ── MINOR: observability / hardening ─────────────────────────────
        params += [
            p(
                "LogLevel", "warn", MIN,
                "debug/info generates a log entry for every request phase event. "
                "At 5000 RPS: info logging = multi-GB/hour log I/O. "
                "'warn' logs only actionable issues — correct for production.",
                "LogLevel warn",
            ),
            p(
                "ErrorLog + CustomLog buffering", "enabled", MIN,
                "Without buffered logging, each request triggers a write() syscall. "
                "At 10K RPS: 10K write() calls/sec. "
                "mod_log_config with buffered I/O reduces log I/O by 95%+.",
                'ErrorLog "logs/error_log"
'
                'CustomLog "logs/access_log" combined
'
                "# Pipe to logger for buffering:
"
                'ErrorLog "|/usr/bin/rotatelogs /var/log/apache2/error_%Y%m%d.log 86400"',
            ),
            p(
                "mod_status + ExtendedStatus", "enabled", MIN,
                "mod_status /server-status exposes: active workers, idle workers, "
                "requests per second, bytes per second, per-request detail. "
                "Essential for capacity planning and detecting slow request accumulation. "
                "Restrict to internal IPs only.",
                "LoadModule status_module modules/mod_status.so
"
                "ExtendedStatus On
"
                "<Location /server-status>
"
                "    SetHandler server-status
"
                "    Require ip 10.0.0.0/8 127.0.0.1
"
                "</Location>",
            ),
            p(
                "Header security (mod_headers)", "enabled", MIN,
                "Security headers prevent common web attacks. "
                "HSTS: forces HTTPS, prevents SSL stripping. "
                "X-Frame-Options: DENY prevents clickjacking. "
                "X-Content-Type-Options: nosniff prevents MIME-type confusion attacks. "
                "Referrer-Policy: controls what's sent in Referer header.",
                'Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
'
                'Header always set X-Frame-Options "DENY"
'
                'Header always set X-Content-Type-Options "nosniff"
'
                'Header always set Referrer-Policy "strict-origin-when-cross-origin"
'
                'Header always unset "X-Powered-By"',
            ),
        ]

        return params

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, mrw: int, sl: int, tpc: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.max_request_workers and ex.max_request_workers < mrw * 0.5:
            findings.append(
                f"[MAJOR] MaxRequestWorkers={ex.max_request_workers} < 50% of "
                f"recommended {mrw}. Apache will return 503 under expected load."
            )
        if (ex.server_limit and ex.threads_per_child and ex.max_request_workers):
            effective_mrw = ex.server_limit * ex.threads_per_child
            if effective_mrw < ex.max_request_workers:
                findings.append(
                    f"[MAJOR] ServerLimit({ex.server_limit}) × ThreadsPerChild({ex.threads_per_child}) "
                    f"= {effective_mrw} < MaxRequestWorkers({ex.max_request_workers}). "
                    "Apache silently caps MaxRequestWorkers at startup. Actual capacity is LOWER than configured."
                )
        if ex.server_tokens and ex.server_tokens.lower() in ("full", "os", "minor", "major"):
            findings.append(
                f"[MAJOR] ServerTokens={ex.server_tokens} exposes Apache version. "
                "Set to 'Prod' to hide version from Server header and error pages."
            )
        if ex.keep_alive and ex.keep_alive.lower() == "off":
            findings.append(
                "[MAJOR] KeepAlive=Off. Every HTTPS request requires a full TLS handshake "
                "(2 RTT ≈ 50–100ms overhead). Enable KeepAlive to eliminate handshake overhead."
            )
        if ex.timeout and ex.timeout > 120:
            findings.append(
                f"[MEDIUM] Timeout={ex.timeout}s. Workers held for {ex.timeout}s by slow clients. "
                "Reduce to 30s to prevent worker exhaustion under traffic spikes."
            )
        if ex.keep_alive_timeout and ex.keep_alive_timeout > 60:
            findings.append(
                f"[MEDIUM] KeepAliveTimeout={ex.keep_alive_timeout}s is excessive. "
                "Each idle keep-alive connection holds a worker. Reduce to 15s."
            )
        if ex.limit_request_line and ex.limit_request_line < 8192:
            findings.append(
                f"[MEDIUM] LimitRequestLine={ex.limit_request_line}. "
                "Long API URLs or JWT in query string will receive 414 errors."
            )
        if self.inp.mpm == "prefork" and (not ex.mpm_model or ex.mpm_model == "prefork"):
            findings.append(
                "[MEDIUM] prefork MPM: 1 process per connection. "
                "RAM-constrained ceiling. Switch to event MPM unless mod_php is required."
            )
        for k, v in ex.os_sysctl.items():
            try:
                if k == "net.core.somaxconn" and int(v) < 512:
                    findings.append(
                        f"[MAJOR] net.core.somaxconn={v}. "
                        "TCP accept queue silently drops connections. Increase to ≥ 65535."
                    )
                if k == "vm.swappiness" and int(v) > 30:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. "
                        "Apache worker processes being swapped causes latency spikes. Reduce to 10."
                    )
            except ValueError:
                pass

        return findings

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> str:
        inp = self.inp
        buf = self._buf()

        ssl_block = ""
        if inp.ssl_enabled:
            ssl_block = (
                "
# ── SSL ─────────────────────────────────────────────────────
"
                "SSLProtocol -all +TLSv1.2 +TLSv1.3
"
                "SSLCipherSuite ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!MD5:!DSS
"
                "SSLHonorCipherOrder on
"
                "SSLCompression off
"
                "SSLUseStapling on
"
                "SSLStaplingCache shmcb:/run/apache2/stapling_cache(131072)
"
                "SSLSessionCache shmcb:/run/apache2/ssl_scache(512000)
"
                "SSLSessionCacheTimeout 600
"
            )

        proxy_block = ""
        if inp.reverse_proxy:
            proxy_block = (
                "
# ── Proxy ────────────────────────────────────────────────────
"
                "ProxyPass        / http://backend:8080/ enablereuse=on
"
                "ProxyPassReverse / http://backend:8080/
"
                "ProxyTimeout 30
"
                "ProxyBadHeader Ignore
"
            )

        static_block = ""
        if inp.serve_static:
            static_block = (
                "
# ── Static file optimisation ─────────────────────────────────
"
                "EnableSendfile on
"
                "EnableMMAP on
"
                "AddOutputFilterByType DEFLATE text/html text/css text/plain "
                "application/json application/javascript
"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Apache HTTPD  [{inp.mode.value.upper():8s}]  "
            f"MPM={inp.mpm.upper()}  cores={inp.cpu_cores}  RAM={inp.ram_gb}GB  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"# ── MPM ──────────────────────────────────────────────────────────
"
            f"LoadModule mpm_{inp.mpm}_module modules/mod_mpm_{inp.mpm}.so

"
            f"<IfModule mpm_{inp.mpm}_module>
"
            f"    ServerLimit              {sl}
"
            f"    MaxRequestWorkers        {mrw}
"
            f"    ThreadsPerChild          {tpc}
"
            f"    MinSpareThreads          {mst}
"
            f"    MaxSpareThreads          {mxst}
"
            f"    StartServers             4
"
            f"    MaxConnectionsPerChild   10000
"
            f"</IfModule>

"
            f"# ── Connection / Keep-Alive ───────────────────────────────────────
"
            f"KeepAlive              On
"
            f"KeepAliveTimeout       15
"
            f"MaxKeepAliveRequests   500
"
            f"Timeout                30

"
            f"# ── Request limits ───────────────────────────────────────────────
"
            f"LimitRequestLine       16384
"
            f"LimitRequestFieldSize  16384
"
            f"LimitRequestFields     150
"
            f"LimitRequestBody       1073741824

"
            f"# ── Buffers ──────────────────────────────────────────────────────
"
            f"SendBufferSize         {buf}
"
            f"ReceiveBufferSize      {buf}

"
            f"# ── Security ─────────────────────────────────────────────────────
"
            f"ServerTokens           Prod
"
            f"ServerSignature        Off
"
            f"TraceEnable            Off
"
            f"{ssl_block}"
            f"{proxy_block}"
            f"{static_block}
"
            f"# ── Logging ──────────────────────────────────────────────────────
"
            f"LogLevel               warn
"
            f'ErrorLog               "logs/error_log"
'
            f'CustomLog              "logs/access_log" combined
'
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> HttpdOutput:
        tpc  = self._tpc()
        mrw  = self._mrw()
        sl   = self._sl(mrw)
        mst  = self._mst(mrw)
        mxst = self._mxst(mrw)

        all_params = self._build_params(mrw, sl, tpc, mst, mxst)

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = mrw,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        return HttpdOutput(
            mode                  = self.inp.mode,
            max_request_workers   = mrw,
            server_limit          = sl,
            threads_per_child     = tpc,
            min_spare_threads     = mst,
            max_spare_threads     = mxst,
            estimated_max_clients = mrw,
            httpd_conf_snippet    = self._render_conf(mrw, sl, tpc, mst, mxst),
            major_params          = major,
            medium_params         = medium,
            minor_params          = minor,
            os_sysctl_conf        = os_engine.sysctl_block(),
            ha_suggestions=[
                "Deploy 2+ HTTPD nodes behind AWS ALB or HAProxy with least_conn.",
                "Use mod_proxy_balancer with bybusyness lbmethod for variable-latency backends.",
                "Shared TLS session cache: use mod_socache_shmcb across workers (same host) "
                "or mod_ssl_ct for multi-node TLS session resumption.",
                "Enable mod_status + Apache Exporter for Prometheus/Grafana dashboards.",
                "Use mod_cache + mod_cache_disk to cache upstream responses at HTTPD layer.",
                "Graceful restart (apachectl graceful) applies most config changes without dropping active connections.",
            ],
            performance_warnings=[w for w in [
                (f"prefork MPM: RAM limit ~{int(self.inp.ram_gb*1024*0.70/_MEM_PREFORK_MB)} processes "
                 f"(with mod_php ~{int(self.inp.ram_gb*1024*0.70/40)} processes at 40MB/proc). "
                 "Switch to event MPM for > 500 concurrent connections.")
                if self.inp.mpm == "prefork" else None,

                (f"expected_concurrent ({self.inp.expected_concurrent}) > MaxRequestWorkers ({mrw}). "
                 "Requests will be rejected (503) under peak load.")
                if self.inp.expected_concurrent > mrw else None,

                "Single CPU core — HTTPD prefork/event both benefit from multiple cores."
                if self.inp.cpu_cores == 1 else None,
            ] if w],
            capacity_warning = self._capacity_warning(
                self.inp.expected_concurrent, mrw, "HTTPD MaxRequestWorkers"
            ),
            audit_findings = self._audit(mrw, sl, tpc)
                             if self.inp.mode == CalcMode.EXISTING else [],
        )


