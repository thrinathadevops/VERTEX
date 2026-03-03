"""
app/calculators/ihs_calculator.py
===================================
IBM HTTP Server (IHS) tuning calculator — NEW and EXISTING modes.

IHS is Apache HTTPD 2.4-based. Key IHS-specific differences:
  1. WebSphere plugin (mod_was_ap22_http / mod_ibm_local_redirector)
     configured via plugin-cfg.xml — NOT mod_proxy / mod_wl_ohs
  2. plugin-cfg.xml: ConnectTimeout, IOTimeout, RetryInterval, MaxConnections
     per WAS/Liberty cluster member
  3. IBM GSKit for SSL (not OpenSSL) — cipher syntax differs
  4. IHS default MaxRequestWorkers = 150 (grossly undersized)
  5. IHS on AIX: worker MPM historically preferred; IHS 9.0+ supports event
  6. Plugin propagation: DMGR pushes plugin-cfg.xml to IHS nodes
     — manual plugin refresh: /opt/IBM/HTTPServer/bin/apachectl -k restart

MaxRequestWorkers formula (event/worker, same as Apache):
  mrw = min(max(expected_concurrent, cpu_cores × 2 × TPC), 16384)

Plugin ConnectTimeout:
  10s — fail fast on dead WAS instances, trigger cluster failover

Plugin IOTimeout:
  avg_request_ms × 3 / 1000, min 30s, max 600s
  Long-running WAS EJB / web service calls may take minutes.

Plugin MaxConnections per WAS member:
  ceil(mrw / was_cluster_size) × 1.5  — 50% headroom above even distribution
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.ihs import IHSInput, IHSOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class IHSCalculator(BaseCalculator):

    def __init__(self, inp: IHSInput) -> None:
        self._require_positive(inp.cpu_cores,           "cpu_cores")
        self._require_positive(inp.ram_gb,              "ram_gb")
        self._require_positive(inp.expected_concurrent, "expected_concurrent")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _tpc(self) -> int:
        return 25

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
        return min(int(self.inp.ram_gb * 1024 * 1024 * 1024 * 0.05), 268_435_456)

    def _plugin_io_timeout(self) -> int:
        """IOTimeout in seconds: avg_request_ms × 3 / 1000, min 30, max 600."""
        return max(30, min(math.ceil(self.inp.avg_request_ms * 3 / 1000), 600))

    def _plugin_max_conns(self, mrw: int) -> int:
        """
        Plugin MaxConnections per WAS member.
        Formula: ceil(mrw / cluster_size) × 1.5 for burst headroom.
        Capped at mrw (no single WAS node should handle all connections).
        """
        per_node = math.ceil(mrw / self.inp.was_cluster_size)
        return min(math.ceil(per_node * 1.5), mrw)

    # ── plugin-cfg.xml snippet renderer ──────────────────────────────────────

    def _render_plugin_cfg(self, mrw: int) -> str:
        inp       = self.inp
        io_to     = self._plugin_io_timeout()
        max_conn  = self._plugin_max_conns(mrw)
        members   = "
".join(
            f'        <Server ConnectTimeout="10" ExtendedHandshake="false" '
            f'MaxConnections="{max_conn}" Name="was{i+1}_9080" '
            f'ServerIOTimeout="{io_to}" WaitForContinue="false">
'
            f'            <Transport Hostname="was{i+1}.example.com" Port="9080" Protocol="http"/>
'
            f'        </Server>'
            for i in range(inp.was_cluster_size)
        )
        ssl_members = "
".join(
            f'        <Server ConnectTimeout="10" ExtendedHandshake="false" '
            f'MaxConnections="{max_conn}" Name="was{i+1}_9443" '
            f'ServerIOTimeout="{io_to}" WaitForContinue="false">
'
            f'            <Transport Hostname="was{i+1}.example.com" Port="9443" Protocol="https">
'
            f'                <Property Name="keyring" Value="/opt/IBM/HTTPServer/ssl/ihskeyring.kdb"/>
'
            f'                <Property Name="stashfile" Value="/opt/IBM/HTTPServer/ssl/ihskeyring.sth"/>
'
            f'            </Transport>
'
            f'        </Server>'
            for i in range(inp.was_cluster_size)
        )

        return (
            f'<!-- ╔══════════════════════════════════════════════════════════════╗ -->
'
            f'<!-- ║  VAREX plugin-cfg.xml  [{inp.mode.value.upper():8s}]  '
            f'Cell={inp.was_cell_name}  Nodes={inp.was_cluster_size}  ║ -->
'
            f'<!-- ╚══════════════════════════════════════════════════════════════╝ -->

'
            f'<!-- Location: /opt/IBM/HTTPServer/Plugins/config/{inp.was_cell_name}/plugin-cfg.xml -->
'
            f'<!-- Propagated from DMGR: {inp.dmgr_host} -->

'
            f'<Config ASDisableNagle="false" AcceptAllContent="false"
'
            f'        AppServerPortPreference="HostHeader"
'
            f'        ChunkedResponse="false"
'
            f'        IISDisableNagle="false" IISPluginPriority="High"
'
            f'        IgnoreDNSFailures="false" RefreshInterval="60"
'
            f'        ResponseChunkSize="64" VHostMatchingCompat="false">

'
            f'    <Log LogLevel="Error"
'
            f'         Name="/opt/IBM/HTTPServer/logs/http_plugin.log"/>

'
            f'    <Property Name="http.maxKeepAliveRequests" Value="500"/>
'
            f'    <Property Name="http.keepAlive" Value="true"/>

'
            f'    <ServerCluster CloneSeparatorChange="false"
'
            f'                   GetDWLMTable="false"
'
            f'                   IgnoreAffinityRequests="true"
'
            f'                   LoadBalance="Round Robin"
'
            f'                   Name="{inp.was_cell_name}_Cluster"
'
            f'                   PostSizeLimit="-1"
'
            f'                   RemoveSpecialHeaders="true"
'
            f'                   RetryInterval="60">

'
            f'        <!-- HTTP members (Port 9080) -->
'
            f'{members}

'
            + (
                f'        <!-- HTTPS members (Port 9443) -->
'
                f'{ssl_members}

'
                if inp.ssl_enabled else ""
            ) +
            f'        <PrimaryServers>
'
            + "
".join(
                f'            <Server Name="was{i+1}_9080"/>'
                for i in range(inp.was_cluster_size)
            ) +
            f'
        </PrimaryServers>
'
            f'    </ServerCluster>

'
            f'    <VirtualHostGroup Name="default_host">
'
            f'        <VirtualHost Name="*:80"/>
'
            f'        <VirtualHost Name="*:443"/>
'
            f'        <VirtualHost Name="*:9080"/>
'
            f'        <VirtualHost Name="*:9443"/>
'
            f'    </VirtualHostGroup>

'
            f'    <UriGroup Name="default_host_Cluster_URIs">
'
            f'        <Uri AffinityCookie="JSESSIONID" AffinityURLIdentifier="jsessionid"
'
            f'             Name="/"/>
'
            f'    </UriGroup>

'
            f'    <Route ServerCluster="{inp.was_cell_name}_Cluster"
'
            f'           UriGroup="default_host_Cluster_URIs"
'
            f'           VirtualHostGroup="default_host"/>
'
            f'</Config>
'
        )

    # ── httpd.conf renderer ───────────────────────────────────────────────────

    def _render_ihs_conf(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> str:
        inp = self.inp
        buf = self._buf()

        plugin_block = ""
        if inp.backend_type in ("was", "liberty"):
            plugin_block = (
                f"
# ── WebSphere Plugin ────────────────────────────────────────────
"
                f"LoadModule was_ap22_http_module "
                f"/opt/IBM/WebSphere/Plugins/bin/64bits/mod_was_ap22_http.so
"
                f"WebSpherePluginConfig "
                f"/opt/IBM/HTTPServer/Plugins/config/{inp.was_cell_name}/plugin-cfg.xml
"
            )

        ssl_block = ""
        if inp.ssl_enabled:
            ssl_block = (
                f"
# ── SSL (IBM GSKit) ─────────────────────────────────────────────
"
                f"LoadModule ibm_ssl_module modules/mod_ibm_ssl.so
"
                f"<IfModule mod_ibm_ssl.c>
"
                f"    Listen 443
"
                f"    <VirtualHost *:443>
"
                f"        SSLEnable
"
                f"        SSLProtocolDisable SSLv2 SSLv3 TLSv1 TLSv1.1
"
                f"        SSLCipherSpec TLS_AES_256_GCM_SHA384
"
                f"        SSLCipherSpec TLS_AES_128_GCM_SHA256
"
                f"        SSLCipherSpec TLS_CHACHA20_POLY1305_SHA256
"
                f"        SSLCipherSpec ECDHE-RSA-AES256-GCM-SHA384
"
                f"        KeyFile /opt/IBM/HTTPServer/ssl/ihskeyring.kdb
"
                f"        SSLStashFile /opt/IBM/HTTPServer/ssl/ihskeyring.sth
"
                f"        SSLTrace off
"
                f"        SSLClientAuth none
"
                f"    </VirtualHost>
"
                f"</IfModule>
"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX IBM HTTP Server  [{inp.mode.value.upper():8s}]  "
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
            f"LimitRequestFieldSize  16384
"
            f"LimitRequestFields     150
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
            f"{plugin_block}
"
            f"# ── Logging ─────────────────────────────────────────────────────
"
            f"LogLevel               warn
"
            f'ErrorLog               "/opt/IBM/HTTPServer/logs/error_log"
'
            f'CustomLog              "/opt/IBM/HTTPServer/logs/access_log" combined
'
        )

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, mrw: int, sl: int, tpc: int, mst: int, mxst: int) -> list:
        ex        = self.inp.existing
        p         = self._p
        inp       = self.inp
        buf       = self._buf()
        io_to     = self._plugin_io_timeout()
        max_conn  = self._plugin_max_conns(mrw)

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "MaxRequestWorkers", str(mrw), M,
                f"Max simultaneous connections = {mrw}. "
                f"IHS default = 150 — install default, severely undersized. "
                f"Formula: max(expected_concurrent={inp.expected_concurrent}, "
                f"cpu_cores×2×TPC={inp.cpu_cores}×2×{tpc}) = {mrw}. "
                "IHS returns 503 immediately when MaxRequestWorkers is exhausted. "
                "Monitor with mod_status /server-status Busy/Idle worker count.",
                f"MaxRequestWorkers {mrw}",
                str(ex.max_request_workers) if ex.max_request_workers else None,
                safe=False,
            ),
            p(
                "ServerLimit", str(sl), M,
                f"Max child processes = ceil({mrw}/{tpc}) + 4 = {sl}. "
                "CRITICAL: IHS silently caps MaxRequestWorkers if "
                "ServerLimit × ThreadsPerChild < MaxRequestWorkers. "
                "Requires full IHS stop/start — not graceful reload.",
                f"ServerLimit {sl}",
                str(ex.server_limit) if ex.server_limit else None,
                safe=False,
            ),
            p(
                "ThreadsPerChild", str(tpc), M,
                f"Threads per child = {tpc} (IHS default, Apache-derived). "
                f"Capacity check: {sl} × {tpc} = {sl * tpc} ≥ MaxRequestWorkers({mrw}). "
                "Silent truncation if capacity < MaxRequestWorkers.",
                f"ThreadsPerChild {tpc}",
                str(ex.threads_per_child) if ex.threads_per_child else None,
                safe=False,
            ),
            p(
                "KeepAlive", "On", M,
                "IHS default is KeepAlive Off. "
                "WAS/Liberty EJB and web service calls use HTTPS — "
                "with KeepAlive Off: every WAS-proxied request requires a new TLS handshake. "
                "Enable KeepAlive to eliminate SSL setup overhead on every request.",
                "KeepAlive On
KeepAliveTimeout 15
MaxKeepAliveRequests 500",
                ex.keep_alive,
            ),
            p(
                "ServerTokens", "Prod", M,
                "IHS default exposes 'IBM_HTTP_Server/<version>' in Server header. "
                "Reveals IHS version, enabling targeted IBM CVE exploitation. "
                "Set Prod + ServerSignature Off + TraceEnable Off.",
                "ServerTokens Prod
ServerSignature Off
TraceEnable Off",
                ex.server_tokens,
            ),
        ]

        if inp.backend_type in ("was", "liberty"):
            params += [
                p(
                    "Plugin ConnectTimeout", "10", MED,
                    "plugin-cfg.xml ConnectTimeout: time to connect to WAS member (seconds). "
                    "Default 5s — too low for WAS JVM GC pause (typical 0.5–3s). "
                    "10s allows GC pause without triggering premature failover. "
                    f"With {inp.was_cluster_size} WAS members: "
                    "on timeout, plugin retries next healthy member automatically.",
                    "<Server ConnectTimeout="10" .../>",
                    str(ex.plugin_connect_timeout) if ex.plugin_connect_timeout else None,
                ),
                p(
                    "Plugin IOTimeout (ServerIOTimeout)", str(io_to), MED,
                    f"plugin-cfg.xml ServerIOTimeout = {io_to}s. "
                    f"Formula: avg_request_ms({inp.avg_request_ms}) × 3 / 1000 "
                    f"= {inp.avg_request_ms * 3 / 1000:.1f}s → clamped to [30, 600] = {io_to}s. "
                    "Time IHS plugin waits for WAS I/O response. "
                    "Too low: long EJB/web service transactions receive 503. "
                    "Too high: hung WAS threads hold IHS workers indefinitely.",
                    f'<Server ServerIOTimeout="{io_to}" .../>',
                    str(ex.plugin_io_timeout) if ex.plugin_io_timeout else None,
                ),
                p(
                    "Plugin MaxConnections", str(max_conn), MED,
                    f"Connections per WAS cluster member = {max_conn}. "
                    f"Formula: ceil(MRW({mrw}) / cluster_size({inp.was_cluster_size})) × 1.5 "
                    f"= ceil({mrw/inp.was_cluster_size:.1f}) × 1.5 = {max_conn}. "
                    "50% headroom above even distribution handles burst + 1 failed node. "
                    "Too low: plugin queues requests when all connections are busy. "
                    "Too high: WAS ExecuteThread pool exhausted.",
                    f'<Server MaxConnections="{max_conn}" .../>',
                    str(ex.plugin_max_connections) if ex.plugin_max_connections else None,
                ),
                p(
                    "Plugin RetryInterval", "60", MED,
                    "plugin-cfg.xml RetryInterval: seconds before retrying a WAS member "
                    "that previously failed. Default 60s. "
                    "Too short (< 30s): IHS keeps hammering a WAS instance still in restart. "
                    "Too long (> 120s): WAS instance that recovered sits idle for too long. "
                    "60s matches typical WAS JVM restart time.",
                    '<ServerCluster RetryInterval="60" .../>',
                    str(ex.plugin_retry_interval) if ex.plugin_retry_interval else None,
                ),
                p(
                    "Plugin Load Balancing", "Round Robin", MED,
                    "plugin-cfg.xml LoadBalance='Round Robin' distributes requests evenly. "
                    "Alternative: 'Random' — avoids hot-spot when one WAS node is slower. "
                    "For session affinity: AffinityCookie='JSESSIONID' in UriGroup "
                    "routes repeat requests from same user to same WAS node.",
                    '<ServerCluster LoadBalance="Round Robin" .../>',
                    ex.plugin_load_balance,
                ),
                p(
                    "Plugin http.keepAlive", "true", MED,
                    "IHS plugin keep-alive to WAS backend. "
                    "Without: each proxied request opens a new socket to WAS. "
                    "At 5000 RPS: 5000 new TCP connections/sec to WAS cluster. "
                    "With http.keepAlive: connections are reused — critical for WAS JVM "
                    "which has limited thread pools (default 50 ExecuteThreads per server).",
                    '<Property Name="http.keepAlive" Value="true"/>
'
                    '<Property Name="http.maxKeepAliveRequests" Value="500"/>',
                ),
            ]

        if inp.ssl_enabled:
            params += [
                p(
                    "IBM GSKit SSL (mod_ibm_ssl)", "TLS 1.2/1.3 only", MED,
                    "IHS uses IBM GSKit for SSL, NOT OpenSSL. "
                    "Configuration uses SSLEnable/SSLProtocolDisable directives "
                    "(not SSLProtocol +TLSv1.3 syntax). "
                    "SSLProtocolDisable: list protocols to DISABLE. "
                    "Disable SSLv2, SSLv3, TLSv1, TLSv1.1 explicitly — "
                    "IBM iKeyman / GSKit doesn't disable them by default.",
                    "SSLEnable
"
                    "SSLProtocolDisable SSLv2 SSLv3 TLSv1 TLSv1.1
"
                    "SSLCipherSpec TLS_AES_256_GCM_SHA384
"
                    "SSLCipherSpec ECDHE-RSA-AES256-GCM-SHA384",
                    ex.ssl_protocol,
                ),
                p(
                    "IHS Key Database (KDB)", "/ssl/ihskeyring.kdb", MED,
                    "IHS uses IBM key database (.kdb) files, NOT PEM/JKS. "
                    "Manage with: iKeyman GUI or IBM MQ pki commands. "
                    "KeyFile: path to .kdb file. "
                    "SSLStashFile: obfuscated password file (.sth). "
                    "Monitor cert expiry: gsk8capicmd_64 -cert -list -db ihskeyring.kdb",
                    "KeyFile /opt/IBM/HTTPServer/ssl/ihskeyring.kdb
"
                    "SSLStashFile /opt/IBM/HTTPServer/ssl/ihskeyring.sth
"
                    "# Create KDB: gsk8capicmd_64 -keydb -create -db ihskeyring.kdb -pw <pwd> -stash
"
                    "# Add cert:   gsk8capicmd_64 -cert -import -db server.p12 -target ihskeyring.kdb",
                ),
            ]

        params += [
            p(
                "Timeout", "30", MED,
                "Default 300s holds IHS workers for 5 minutes. Reduce to 30s.",
                "Timeout 30",
                str(ex.timeout) if ex.timeout else None,
            ),
            p(
                "KeepAliveTimeout", "15", MED,
                "15s idle keep-alive timeout. IHS default may be 300s (5 minutes). "
                "Each idle keep-alive connection holds an IHS thread.",
                "KeepAliveTimeout 15",
                str(ex.keep_alive_timeout) if ex.keep_alive_timeout else None,
            ),
            p(
                "LimitRequestFieldSize", "16384", MED,
                "16KB per-header value. WAS LTPA tokens (SSO) are ~2–4KB. "
                "WAS cookie-based session: ~1KB. SAML assertions: up to 16KB.",
                "LimitRequestFieldSize 16384",
                str(ex.limit_request_field_size) if ex.limit_request_field_size else None,
            ),
            p(
                "SendBufferSize", str(buf), MED,
                f"TCP send buffer = 5% RAM = {buf:,} bytes.",
                f"SendBufferSize {buf}
ReceiveBufferSize {buf}",
            ),
            p(
                "LogLevel", "warn", MIN,
                "IHS default can be 'debug' on freshly installed nodes. "
                "Set to 'warn' for production.",
                "LogLevel warn",
            ),
            p(
                "Plugin log level", "Error", MIN,
                "plugin-cfg.xml LogLevel='Error'. "
                "Debug generates gigabytes/hour at production traffic levels. "
                "Increase to 'Trace' only when troubleshooting plugin routing issues.",
                '<Log LogLevel="Error" Name="/opt/IBM/HTTPServer/logs/http_plugin.log"/>',
            ),
            p(
                "mod_status", "enabled (restricted)", MIN,
                "IHS mod_status /server-status: live worker utilisation. "
                "Essential for monitoring IHS → WAS proxy queue depth. "
                "Restrict to admin/monitoring subnet.",
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
                "Security headers", "enabled", MIN,
                "IHS out-of-box ships without security headers. "
                "Add via mod_headers — required by IBM security hardening guide.",
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
            p(
                "Plugin propagation (DMGR)", "auto-push enabled", MIN,
                f"DMGR ({inp.dmgr_host}) automatically pushes plugin-cfg.xml to IHS nodes "
                "when WAS cluster membership changes. "
                "Verify: AdminConsole → Environment → Update Web Server Plugin. "
                "Manual refresh: /opt/IBM/HTTPServer/bin/apachectl -k graceful",
                f"# Propagation command (run on DMGR as wasadmin):
"
                f"# wsadmin -lang jython -c "
                f""AdminTask.propagatePluginCfg(['-webserver', 'webserver1'])"
"
                f"# Plugin cfg location: /opt/IBM/HTTPServer/Plugins/config/"
                f"{inp.was_cell_name}/plugin-cfg.xml",
            ),
        ]

        return params

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, mrw: int, sl: int, tpc: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.max_request_workers and ex.max_request_workers <= 150:
            findings.append(
                f"[MAJOR] MaxRequestWorkers={ex.max_request_workers} — IHS install default. "
                f"Production-unsafe. Recommended: {mrw}."
            )
        if ex.server_limit and ex.threads_per_child and ex.max_request_workers:
            cap = ex.server_limit * ex.threads_per_child
            if cap < ex.max_request_workers:
                findings.append(
                    f"[MAJOR] ServerLimit({ex.server_limit}) × ThreadsPerChild({ex.threads_per_child}) "
                    f"= {cap} < MaxRequestWorkers({ex.max_request_workers}). "
                    "IHS silently caps workers. Effective capacity = "
                    f"{cap}, not {ex.max_request_workers}."
                )
        if ex.keep_alive and ex.keep_alive.lower() == "off":
            findings.append(
                "[MAJOR] KeepAlive=Off. Every HTTPS request requires a full SSL handshake. "
                "WAS LTPA/SSO cookie re-negotiation adds overhead per request. Enable immediately."
            )
        if ex.server_tokens and ex.server_tokens.lower() not in ("prod", "minimal"):
            findings.append(
                f"[MAJOR] ServerTokens={ex.server_tokens} exposes IHS version. "
                "IBM IHS version exposed enables targeted CVE attacks. Set to Prod."
            )
        if ex.timeout and ex.timeout > 120:
            findings.append(
                f"[MEDIUM] Timeout={ex.timeout}s. IHS workers held {ex.timeout}s by slow clients. "
                "Reduce to 30s."
            )
        if ex.plugin_connect_timeout and ex.plugin_connect_timeout < 5:
            findings.append(
                f"[MEDIUM] plugin ConnectTimeout={ex.plugin_connect_timeout}s. "
                "Too low — WAS JVM GC pause (0.5–3s) triggers premature failover. "
                "Increase to 10s."
            )
        if ex.plugin_io_timeout and ex.plugin_io_timeout > 300:
            findings.append(
                f"[MEDIUM] plugin IOTimeout={ex.plugin_io_timeout}s ({ex.plugin_io_timeout//60}min). "
                "Excessive — hung WAS threads hold IHS workers too long. "
                f"Recommended: {self._plugin_io_timeout()}s."
            )
        if ex.plugin_max_connections:
            mrw_calc = self._mrw()
            rec = self._plugin_max_conns(mrw_calc)
            if ex.plugin_max_connections < rec * 0.5:
                findings.append(
                    f"[MEDIUM] plugin MaxConnections={ex.plugin_max_connections} per WAS member. "
                    f"Too low — plugin queues requests beyond this limit. "
                    f"Recommended: {rec}."
                )
        if ex.ssl_protocol:
            for weak in ("TLSv1 ", "TLSv1.1", "SSLv3", "SSLv2"):
                if weak in ex.ssl_protocol:
                    findings.append(
                        f"[MAJOR] ssl_protocol enables deprecated {weak.strip()}. "
                        "IBM Security Alert mandates TLS ≥ 1.2. Disable via SSLProtocolDisable."
                    )
        if ex.keep_alive_timeout and ex.keep_alive_timeout > 60:
            findings.append(
                f"[MEDIUM] KeepAliveTimeout={ex.keep_alive_timeout}s. "
                "Idle connections hold IHS workers. Reduce to 15s."
            )
        for k, v in ex.os_sysctl.items():
            try:
                if k == "net.core.somaxconn" and int(v) < 512:
                    findings.append(
                        f"[MAJOR] net.core.somaxconn={v}. "
                        "OS accept queue starved. Increase to ≥ 65535."
                    )
                if k == "vm.swappiness" and int(v) > 20:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. IHS worker processes "
                        "being paged to disk causes latency spikes. Reduce to 10."
                    )
            except ValueError:
                pass

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> IHSOutput:
        tpc      = self._tpc()
        mrw      = self._mrw()
        sl       = self._sl(mrw)
        mst      = self._mst(mrw)
        mxst     = self._mxst(mrw)
        io_to    = self._plugin_io_timeout()
        max_conn = self._plugin_max_conns(mrw)

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

        return IHSOutput(
            mode                  = self.inp.mode,
            max_request_workers   = mrw,
            server_limit          = sl,
            threads_per_child     = tpc,
            min_spare_threads     = mst,
            max_spare_threads     = mxst,
            estimated_max_clients = mrw,
            plugin_connect_timeout= 10,
            plugin_io_timeout     = io_to,
            plugin_max_connections= max_conn,
            ihs_conf_snippet      = self._render_ihs_conf(mrw, sl, tpc, mst, mxst),
            plugin_cfg_snippet    = self._render_plugin_cfg(mrw)
                                    if self.inp.backend_type in ("was", "liberty")
                                    else "<!-- backend_type=none/custom: no plugin-cfg.xml generated -->",
            major_params          = major,
            medium_params         = medium,
            minor_params          = minor,
            os_sysctl_conf        = os_engine.sysctl_block(),
            ha_suggestions=[
                f"Deploy {max(2, self.inp.was_cluster_size)} IHS nodes behind IBM DataPower "
                "or F5 BIG-IP for HA.",
                "Use WebSphere DMGR to automatically propagate plugin-cfg.xml to all IHS nodes "
                "when WAS cluster topology changes.",
                "IHS plugin RetryInterval=60s: after WAS node restart, plugin re-routes "
                "traffic automatically within 60s.",
                "Configure WAS session persistence (database or memory-to-memory replication) "
                "so IHS failover doesn't lose user sessions.",
                "Monitor IHS → WAS proxy health via mod_status + IBM HTTP Server Toolkit "
                "or IBM Performance Management (IBM APM).",
                "IBM HTTP Server on AIX: set LimitRequestBody and ensure ulimit -n (file descriptors) "
                "≥ MaxRequestWorkers × 2 + 64.",
            ],
            performance_warnings=[w for w in [
                (f"expected_concurrent ({self.inp.expected_concurrent}) > MaxRequestWorkers ({mrw}). "
                 "IHS will return 503 under peak load.")
                if self.inp.expected_concurrent > mrw else None,
                "IHS on AIX: worker MPM historically preferred over event. "
                "Verify event MPM stability for your AIX + IHS version combination."
                if self.inp.os_type.value == "aix" else None,
            ] if w],
            capacity_warning      = self._capacity_warning(
                self.inp.expected_concurrent, mrw, "IHS MaxRequestWorkers"
            ),
            audit_findings        = self._audit(mrw, sl, tpc)
                                    if self.inp.mode == CalcMode.EXISTING else [],
        )
