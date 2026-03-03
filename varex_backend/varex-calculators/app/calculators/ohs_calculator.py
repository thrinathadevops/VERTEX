"""
app/calculators/ohs_calculator.py
===================================
Oracle HTTP Server (OHS) tuning calculator — NEW and EXISTING modes.

OHS is Apache HTTPD 2.4-based. Key OHS-specific differences vs vanilla HTTPD:
  1. mod_wl_ohs  — Oracle WebLogic proxy module (not mod_proxy)
  2. OHS 12c supports only event and worker MPM (prefork removed)
  3. Fusion Apps / Oracle SSO uses oversized SAML assertion headers
     requiring LimitRequestFieldSize ≥ 32768 and large header buffers
  4. WLConnectTimeout / WLIOTimeout — WebLogic-specific timeout params
  5. OHS default MaxRequestWorkers = 150 (grossly undersized for production)
  6. Oracle recommends ServerLimit × ThreadsPerChild ≥ MaxRequestWorkers
     — same silent truncation issue as vanilla HTTPD

MaxRequestWorkers formula (same as HTTPD event/worker):
  mrw = min(max(expected_concurrent, cpu_cores × 2 × TPC), 16384)

WLConnectTimeout recommendation:
  10000ms (10s) — fail fast on dead WLS instances, trigger cluster failover

WLIOTimeout recommendation:
  avg_request_ms × 3 (3× headroom), min 30000ms, max 600000ms
  Long-running Fusion App transactions may take minutes — don't set too low.
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.ohs import OHSInput, OHSOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class OHSCalculator(BaseCalculator):

    def __init__(self, inp: OHSInput) -> None:
        self._require_positive(inp.cpu_cores,            "cpu_cores")
        self._require_positive(inp.ram_gb,               "ram_gb")
        self._require_positive(inp.expected_concurrent,  "expected_concurrent")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _tpc(self) -> int:
        return 25  # OHS 12c: event/worker only, default TPC = 25

    def _mrw(self) -> int:
        thread_based = self.inp.cpu_cores * 2 * self._tpc()
        return min(max(self.inp.expected_concurrent, thread_based), 16_384)

    def _sl(self, mrw: int) -> int:
        return math.ceil(mrw / self._tpc()) + 4

    def _mst(self, mrw: int) -> int:
        return max(10, mrw // 10)

    def _mxst(self, mrw: int) -> int:
        return max(75, mrw // 4)

    def _buf(self) -> int:
        """5% RAM for TCP buffers, capped at 256MB."""
        return min(int(self.inp.ram_gb * 1024 * 1024 * 1024 * 0.05), 268_435_456)

    def _wl_io_timeout(self) -> int:
        """
        WLIOTimeout: avg_request_ms × 3, min 30s, max 600s.
        Fusion Apps long-running transactions can legitimately take 60–300s.
        Too low → WLS returns 504 mid-transaction.
        Too high → OHS holds a thread indefinitely on hung WLS instances.
        """
        val = max(30_000, min(self.inp.avg_request_ms * 3, 600_000))
        return val

    def _limit_field_size(self) -> int:
        """
        Fusion Apps / Oracle SSO: SAML assertions and OAM tokens can reach 32KB.
        Standard apps: 16KB is sufficient.
        """
        return 32_768 if self.inp.fusion_apps else 16_384

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> list:
        ex         = self.inp.existing
        p          = self._p
        inp        = self.inp
        buf        = self._buf()
        wl_io      = self._wl_io_timeout()
        lfs        = self._limit_field_size()

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "MaxRequestWorkers", str(mrw), M,
                f"Maximum simultaneous connections = {mrw}. "
                f"OHS default = 150 — severely undersized for production. "
                f"Formula: max(expected_concurrent={inp.expected_concurrent}, "
                f"cpu_cores×2×TPC={inp.cpu_cores}×2×{tpc}) = {mrw}. "
                "OHS returns 503 immediately when MaxRequestWorkers is exhausted. "
                "Monitor with mod_status /server-status Busy/Idle ratio.",
                f"MaxRequestWorkers {mrw}",
                str(ex.max_request_workers) if ex.max_request_workers else None,
                safe=False,
            ),
            p(
                "ServerLimit", str(sl), M,
                f"Max child processes = {sl} = ceil({mrw}/{tpc}) + 4. "
                "CRITICAL: OHS (like Apache) silently caps MaxRequestWorkers if "
                "ServerLimit × ThreadsPerChild < MaxRequestWorkers. "
                "Verify on startup: grep -i 'server limit' /path/ohs/logs/error_log. "
                "Requires full OHS restart (not reload) to take effect.",
                f"ServerLimit {sl}",
                str(ex.server_limit) if ex.server_limit else None,
                safe=False,
            ),
            p(
                "ThreadsPerChild", str(tpc), M,
                f"Worker threads per child = {tpc} (OHS default, Apache-derived). "
                f"Total capacity = ServerLimit × TPC = {sl} × {tpc} = {sl * tpc}. "
                "Must satisfy: ServerLimit × ThreadsPerChild ≥ MaxRequestWorkers. "
                "If not: OHS silently truncates MaxRequestWorkers at startup.",
                f"ThreadsPerChild {tpc}",
                str(ex.threads_per_child) if ex.threads_per_child else None,
                safe=False,
            ),
            p(
                "ServerTokens", "Prod", M,
                "OHS default exposes version in Server header (e.g. 'Oracle-HTTP-Server/12.2.1.4.0'). "
                "This reveals OHS version, facilitating targeted Oracle CVE attacks. "
                "Set to 'Prod' for minimal disclosure. "
                "Also set ServerSignature Off and TraceEnable Off.",
                "ServerTokens Prod
ServerSignature Off
TraceEnable Off",
                ex.server_tokens,
            ),
            p(
                "KeepAlive", "On", M,
                "OHS default is KeepAlive Off (unlike standard Apache). "
                "With KeepAlive Off: every HTTPS request from browser "
                "requires a new TLS handshake (2 RTT ≈ 50–100ms). "
                "Oracle Fusion Apps pages load 50–200 assets — "
                "with KeepAlive Off: 50–200 TLS handshakes per page load. "
                "Enable immediately for any browser-facing OHS deployment.",
                "KeepAlive On
KeepAliveTimeout 15
MaxKeepAliveRequests 500",
                ex.keep_alive,
            ),

            # ── MEDIUM: WebLogic proxy ────────────────────────────────────
        ]

        if inp.backend_type in ("weblogic", "fusion"):
            params += [
                p(
                    "WLConnectTimeout", "10000", MED,
                    "mod_wl_ohs: time to establish connection to WebLogic Managed Server (ms). "
                    "Default 10ms is dangerously low — OHS gives up before WLS has started. "
                    "10000ms (10s): allows WLS startup, GC pause, or network transient. "
                    "When timeout exceeded, OHS automatically fails over to next WLS in cluster. "
                    f"With {inp.wls_cluster_size} WLS nodes: failover latency ≤ 10s.",
                    "WLConnectTimeout 10000",
                    str(ex.wl_connect_timeout) if ex.wl_connect_timeout else None,
                ),
                p(
                    "WLIOTimeout", str(wl_io), MED,
                    f"mod_wl_ohs: max time to wait for WebLogic response = {wl_io}ms. "
                    f"Formula: avg_request_ms({inp.avg_request_ms}) × 3 = {inp.avg_request_ms*3}ms, "
                    f"clamped to [30000, 600000] = {wl_io}ms. "
                    "Too low: long-running Fusion transactions receive 504. "
                    "Fusion Apps report generation, batch jobs: may need 300000ms+. "
                    "Too high: OHS holds a thread indefinitely on hung WLS instances. "
                    "Monitor WLS thread dump to distinguish slow vs hung requests.",
                    f"WLIOTimeout {wl_io}",
                    str(ex.wl_io_timeout) if ex.wl_io_timeout else None,
                ),
                p(
                    "WebLogicCluster", f"wls1:7001,wls2:7001", MED,
                    f"Define all {inp.wls_cluster_size} WebLogic Managed Server addresses. "
                    "mod_wl_ohs uses round-robin with automatic failover. "
                    "DynamicServerList Off: prevents mod_wl_ohs from dynamically adding "
                    "WLS nodes that haven't been explicitly configured. "
                    "Recommended: use WLS cluster DNS name if available.",
                    "WebLogicCluster wls1:7001,wls2:7001
"
                    "DynamicServerList Off
"
                    "WLLogFile /u01/oracle/ohs/logs/wl_proxy.log",
                ),
                p(
                    "WLProxySSL / WLProxySSLPassThrough", "Off / On", MED,
                    "WLProxySSL Off: OHS terminates SSL, forwards plain HTTP to WLS. "
                    "Offloads TLS computation from WLS JVM (significant CPU saving). "
                    "WLProxySSLPassThrough On: forward original client SSL info to WLS "
                    "via WL-Proxy-SSL header (required for WLS applications that check "
                    "request.isSecure() or redirect to HTTPS).",
                    "WLProxySSL Off
WLProxySSLPassThrough On",
                ),
            ]

        # ── MEDIUM: connection / header / buffer tuning ───────────────────
        params += [
            p(
                "Timeout", "30", MED,
                "OHS default 300s holds workers for 5 minutes on slow clients. "
                "30s frees workers 10× faster. "
                "For Fusion Apps long-running transactions: increase to 120s "
                "but ensure WLIOTimeout is set lower (e.g. 90000ms) to fail fast "
                "on hung WLS before OHS timeout fires.",
                "Timeout 30",
                str(ex.timeout) if ex.timeout else None,
            ),
            p(
                "KeepAliveTimeout", "15", MED,
                "15s idle keep-alive timeout. "
                "Oracle Fusion Apps UI makes 50–200 asset requests per page — "
                "15s gives enough window for parallel browser requests to complete "
                "without holding connections indefinitely.",
                "KeepAliveTimeout 15",
                str(ex.keep_alive_timeout) if ex.keep_alive_timeout else None,
            ),
            p(
                "LimitRequestFieldSize", str(lfs), MED,
                f"Per-header value size limit = {lfs} bytes. "
                + (
                    "Fusion Apps / Oracle SSO: SAML assertions in HTTP headers can reach "
                    "16–32KB. OAM (Oracle Access Manager) tokens + Fusion session cookies "
                    "routinely exceed 16KB. "
                    "With default 8KB: OAM SSO redirects fail with 400 Bad Request. "
                    "Set to 32768 for all Fusion Apps / OAM-protected OHS instances."
                    if inp.fusion_apps else
                    "Standard apps with JWT Authorization headers (2–8KB). "
                    "16384 bytes covers most REST API + SAML-lite use cases."
                ),
                f"LimitRequestFieldSize {lfs}",
                str(ex.limit_request_field_size) if ex.limit_request_field_size else None,
            ),
            p(
                "LimitRequestLine", "16384", MED,
                "Default 8KB. OHS serving Fusion Apps / ADF faces URLs with long "
                "encoded state parameters (ADF view state in URL = 4–12KB). "
                "16KB prevents 414 errors on ADF-based Fusion pages.",
                "LimitRequestLine 16384",
                str(ex.limit_request_line) if ex.limit_request_line else None,
            ),
            p(
                "SendBufferSize", str(buf), MED,
                f"TCP send buffer = 5% RAM = {buf:,} bytes. "
                "Fusion Apps pages with large JavaScript bundles and report outputs "
                "benefit from larger send buffers reducing write() syscall count.",
                f"SendBufferSize {buf}
ReceiveBufferSize {buf}",
                str(ex.wl_io_timeout) if ex.wl_io_timeout else None,
            ),
        ]

        # ── SSL params ────────────────────────────────────────────────────
        if inp.ssl_enabled:
            params += [
                p(
                    "SSLProtocol", "TLSv1.2 TLSv1.3", MED,
                    "OHS older versions may default to TLSv1.0/1.1. "
                    "PCI-DSS and Oracle Security Alert mandates TLS ≥ 1.2. "
                    "TLSv1.3: 1-RTT handshake — critical for Fusion Apps which "
                    "open 50–200 connections per page load.",
                    "SSLProtocol -all +TLSv1.2 +TLSv1.3",
                    ex.ssl_protocols,
                ),
                p(
                    "SSLSessionCache", "shmcb (512KB)", MED,
                    "Shared TLS session cache across all OHS worker processes. "
                    "Fusion Apps: browsers reconnect frequently (SPA navigation, "
                    "background polling). Session resumption eliminates 2-RTT overhead "
                    "on every reconnect, critical for sub-second page load targets.",
                    "SSLSessionCache shmcb:/u01/oracle/ohs/logs/ssl_scache(524288)
"
                    "SSLSessionCacheTimeout 600
"
                    "SSLUseStapling on
"
                    "SSLStaplingCache shmcb:/u01/oracle/ohs/logs/ssl_stapling(131072)",
                ),
                p(
                    "OracleWallet / SSL Certificate", "Oracle Wallet", MED,
                    "OHS uses Oracle Wallet (orapki) for certificate management, "
                    "not PEM files like vanilla Apache. "
                    "Wallet auto-login (cwallet.sso) enables OHS to start without "
                    "password prompts in automated/systemd environments. "
                    "Monitor wallet expiry: orapki wallet display -wallet /path/to/wallet",
                    "SSLWallet /u01/oracle/ohs/config/fmwconfig/components/OHS/<name>/keystores/default
"
                    "# Create wallet: orapki wallet create -wallet /path -pwd <pwd> -auto_login
"
                    "# Add cert: orapki wallet add -wallet /path -trusted_cert -cert server.crt",
                ),
            ]

        # ── Fusion Apps specific ──────────────────────────────────────────
        if inp.fusion_apps:
            params += [
                p(
                    "LimitRequestFields", "200", MED,
                    "Default Apache limit = 100 headers. "
                    "Oracle Fusion Apps / ADF pages send large numbers of custom headers: "
                    "OAM tokens, ADF state headers, Oracle SSO cookies, WLS proxy headers. "
                    "Exceeding 100 → 400 Bad Request on complex Fusion pages. "
                    "Set to 200 for all Fusion-facing OHS instances.",
                    "LimitRequestFields 200",
                ),
                p(
                    "RLimitMEM / RLimitCPU", "set", MED,
                    "Resource limits per CGI/worker process. "
                    "Fusion Apps CGI extensions and mod_plsql processes should be "
                    "resource-limited to prevent runaway processes consuming host memory. "
                    "RLimitMEM in bytes; RLimitCPU in seconds.",
                    f"RLimitMEM {int(self.inp.ram_gb * 1024 * 1024 * 1024 * 0.10)} "
                    f"{int(self.inp.ram_gb * 1024 * 1024 * 1024 * 0.15)}
"
                    "RLimitCPU 60 120",
                ),
            ]

        # ── MINOR: observability / hardening ─────────────────────────────
        params += [
            p(
                "LogLevel", "warn", MIN,
                "OHS default can be 'debug' in FMW installations. "
                "Debug logging generates gigabytes/hour at production traffic. "
                "Set to 'warn' for production. Keep 'info' only during initial rollout.",
                "LogLevel warn",
            ),
            p(
                "mod_status", "enabled (restricted)", MIN,
                "OHS mod_status /server-status: real-time worker utilisation. "
                "Restrict to OHS admin / monitoring subnet only. "
                "Essential for WebLogic proxy monitoring: observe WL request queue depth.",
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
                "OHS Component Log rotation", "enabled", MIN,
                "OHS writes component logs under $DOMAIN_HOME/servers/ohs_name/logs/. "
                "Without rotation, diagnostic.log grows unbounded. "
                "Configure ODL (Oracle Diagnostics Logging) rotation via EM or "
                "logconfig.xml in FMW config.",
                "# Configure in: $DOMAIN_HOME/config/fmwconfig/components/OHS/<name>/logging.xml
"
                "# Set: maxFileSize=100MB maxRetainedFiles=10",
            ),
            p(
                "Security headers (mod_headers)", "enabled", MIN,
                "OHS out-of-box does NOT set security headers. "
                "Required by Oracle Security Compliance (FMW hardening guide). "
                "HSTS mandatory if OHS terminates TLS.",
                'Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
'
                'Header always set X-Frame-Options "SAMEORIGIN"
'
                'Header always set X-Content-Type-Options "nosniff"
'
                'Header always unset "X-Powered-By"
'
                'Header always unset "Server"',
            ),
        ]

        return params

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, mrw: int, sl: int, tpc: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.max_request_workers and ex.max_request_workers <= 150:
            findings.append(
                f"[MAJOR] MaxRequestWorkers={ex.max_request_workers} — this is the OHS "
                "install default. Severely undersized for production. "
                f"Recommended: {mrw}."
            )
        if ex.server_limit and ex.threads_per_child and ex.max_request_workers:
            cap = ex.server_limit * ex.threads_per_child
            if cap < ex.max_request_workers:
                findings.append(
                    f"[MAJOR] ServerLimit({ex.server_limit}) × ThreadsPerChild({ex.threads_per_child}) "
                    f"= {cap} < MaxRequestWorkers({ex.max_request_workers}). "
                    "OHS silently caps actual workers at startup. Effective capacity = "
                    f"{cap}, not {ex.max_request_workers}."
                )
        if ex.keep_alive and ex.keep_alive.lower() == "off":
            findings.append(
                "[MAJOR] KeepAlive=Off. OHS default. Every browser request requires "
                "full TLS handshake. Fusion Apps pages make 50–200 asset requests — "
                "each with a new TLS handshake. Enable immediately."
            )
        if ex.server_tokens and ex.server_tokens.lower() not in ("prod", "minimal"):
            findings.append(
                f"[MAJOR] ServerTokens={ex.server_tokens} exposes OHS/Apache version. "
                "Set to Prod."
            )
        if ex.timeout and ex.timeout > 120:
            findings.append(
                f"[MEDIUM] Timeout={ex.timeout}s. Workers held for {ex.timeout}s by slow clients. "
                "Reduce to 30–60s (or match WLIOTimeout if WebLogic proxy)."
            )
        if ex.wl_io_timeout and ex.wl_io_timeout > 300_000:
            findings.append(
                f"[MEDIUM] WLIOTimeout={ex.wl_io_timeout}ms ({ex.wl_io_timeout//1000}s). "
                "Excessive — hung WLS instances will hold OHS threads for 5+ minutes. "
                f"Recommended: {self._wl_io_timeout()}ms."
            )
        if ex.wl_connect_timeout and ex.wl_connect_timeout < 5000:
            findings.append(
                f"[MEDIUM] WLConnectTimeout={ex.wl_connect_timeout}ms is very low. "
                "WLS GC pause or brief network transient will cause premature failover. "
                "Increase to 10000ms."
            )
        if ex.ssl_protocols:
            for weak in ("TLSv1 ", "TLSv1.1", "SSLv3", "SSLv2"):
                if weak in ex.ssl_protocols:
                    findings.append(
                        f"[MAJOR] ssl_protocols contains deprecated {weak.strip()}. "
                        "Oracle Security Alert mandates TLS ≥ 1.2. Remove immediately."
                    )
        if ex.keep_alive_timeout and ex.keep_alive_timeout > 60:
            findings.append(
                f"[MEDIUM] KeepAliveTimeout={ex.keep_alive_timeout}s. "
                "Idle connections hold OHS workers. Reduce to 15s."
            )
        for k, v in ex.os_sysctl.items():
            try:
                if k == "net.core.somaxconn" and int(v) < 512:
                    findings.append(
                        f"[MAJOR] net.core.somaxconn={v}. "
                        "OS accept queue drops connections under burst. Increase to ≥ 65535."
                    )
                if k == "vm.swappiness" and int(v) > 20:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. OHS worker processes "
                        "being paged to disk causes latency spikes. Reduce to 10."
                    )
            except ValueError:
                pass

        return findings

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> str:
        inp    = self.inp
        buf    = self._buf()
        wl_io  = self._wl_io_timeout()
        lfs    = self._limit_field_size()

        wl_block = ""
        if inp.backend_type in ("weblogic", "fusion"):
            wl_block = (
                f"
# ── mod_wl_ohs: WebLogic Proxy ────────────────────────────────
"
                f"LoadModule weblogic_module modules/mod_wl_ohs.so

"
                f"<IfModule mod_weblogic.c>
"
                f"    WebLogicCluster  wls1:7001,wls2:7001
"
                f"    DynamicServerList Off
"
                f"    WLConnectTimeout 10000
"
                f"    WLIOTimeout      {wl_io}
"
                f"    WLProxySSL       Off
"
                f"    WLProxySSLPassThrough On
"
                f"    WLLogFile        /u01/oracle/ohs/logs/wl_proxy.log
"
                f"</IfModule>
"
            )

        ssl_block = ""
        if inp.ssl_enabled:
            ssl_block = (
                f"
# ── SSL ────────────────────────────────────────────────────────
"
                f"SSLProtocol -all +TLSv1.2 +TLSv1.3
"
                f"SSLCipherSuite ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!MD5:!DSS
"
                f"SSLHonorCipherOrder on
"
                f"SSLSessionCache shmcb:/u01/oracle/ohs/logs/ssl_scache(524288)
"
                f"SSLSessionCacheTimeout 600
"
                f"SSLUseStapling on
"
                f"SSLStaplingCache shmcb:/u01/oracle/ohs/logs/ssl_stapling(131072)
"
                f"SSLWallet /u01/oracle/ohs/config/fmwconfig/components/OHS/ohs1/keystores/default
"
            )

        fusion_block = ""
        if inp.fusion_apps:
            fusion_block = (
                f"
# ── Fusion Apps specifics ──────────────────────────────────────
"
                f"LimitRequestFields 200
"
                f"LimitRequestFieldSize {lfs}
"
                f"RLimitMEM {int(inp.ram_gb*1024*1024*1024*0.10)} "
                f"{int(inp.ram_gb*1024*1024*1024*0.15)}
"
                f"RLimitCPU 60 120
"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Oracle HTTP Server [{inp.mode.value.upper():8s}]  "
            f"MPM={inp.mpm.upper()}  RAM={inp.ram_gb}GB  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"# ── MPM ─────────────────────────────────────────────────────────
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
            f"# ── Connection ──────────────────────────────────────────────────
"
            f"KeepAlive              On
"
            f"KeepAliveTimeout       15
"
            f"MaxKeepAliveRequests   500
"
            f"Timeout                30

"
            f"# ── Request limits ──────────────────────────────────────────────
"
            f"LimitRequestLine       16384
"
            f"LimitRequestFieldSize  {lfs}
"
            f"LimitRequestFields     {200 if inp.fusion_apps else 150}
"
            f"LimitRequestBody       1073741824

"
            f"# ── Buffers ─────────────────────────────────────────────────────
"
            f"SendBufferSize         {buf}
"
            f"ReceiveBufferSize      {buf}

"
            f"# ── Security ────────────────────────────────────────────────────
"
            f"ServerTokens           Prod
"
            f"ServerSignature        Off
"
            f"TraceEnable            Off
"
            f"{ssl_block}"
            f"{wl_block}"
            f"{fusion_block}
"
            f"# ── Logging ─────────────────────────────────────────────────────
"
            f"LogLevel               warn
"
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> OHSOutput:
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

        ha_suggestions = [
            f"Deploy {max(2, self.inp.wls_cluster_size)} OHS nodes behind Oracle Traffic Director (OTD) "
            "or F5 BIG-IP for HA.",
            "Use WebLogicCluster with all WLS Managed Server addresses — "
            "mod_wl_ohs performs automatic failover when a WLS node is unreachable.",
            "Configure WLS cluster multicast or unicast replication for HTTP session HA.",
            "OHS 12c: use WebLogic Dynamic Clusters for elastic WLS scaling "
            "with DynamicServerList On for automatic node discovery.",
            "Monitor via OHS built-in Fusion Middleware Control (EM) metrics: "
            "active requests, WLS proxy queue depth, SSL handshake rate.",
            "Use Oracle Access Manager (OAM) mod_osso / mod_oblix for SSO HA "
            "with multiple OAM Server nodes in the policy domain.",
        ]
        if self.inp.fusion_apps:
            ha_suggestions.append(
                "Fusion Apps: OHS must be co-located in same data centre as WLS nodes. "
                "WAN-separated OHS→WLS proxy adds latency to every ADF state transfer."
            )

        return OHSOutput(
            mode                  = self.inp.mode,
            max_request_workers   = mrw,
            server_limit          = sl,
            threads_per_child     = tpc,
            min_spare_threads     = mst,
            max_spare_threads     = mxst,
            estimated_max_clients = mrw,
            ohs_conf_snippet      = self._render_conf(mrw, sl, tpc, mst, mxst),
            major_params          = major,
            medium_params         = medium,
            minor_params          = minor,
            os_sysctl_conf        = os_engine.sysctl_block(),
            ha_suggestions        = ha_suggestions,
            performance_warnings  = [w for w in [
                ("OHS 12c does not support prefork MPM. Use event or worker.")
                if hasattr(self.inp, "mpm") and self.inp.mpm == "prefork" else None,
                (f"Fusion Apps + WLIOTimeout={self._wl_io_timeout()}ms: ensure WLS ExecuteThread "
                 "count matches OHS MaxRequestWorkers to avoid proxy queue buildup.")
                if self.inp.fusion_apps else None,
                (f"expected_concurrent ({self.inp.expected_concurrent}) > MaxRequestWorkers ({mrw}). "
                 "OHS will return 503 under peak load.")
                if self.inp.expected_concurrent > mrw else None,
            ] if w],
            capacity_warning      = self._capacity_warning(
                self.inp.expected_concurrent, mrw, "OHS MaxRequestWorkers"
            ),
            audit_findings        = self._audit(mrw, sl, tpc)
                                    if self.inp.mode == CalcMode.EXISTING else [],
        )
