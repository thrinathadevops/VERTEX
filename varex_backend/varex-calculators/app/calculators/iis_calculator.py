"""
app/calculators/iis_calculator.py
===================================
IIS tuning calculator — NEW and EXISTING modes.

IIS threading model (fundamentally different from Apache):
─────────────────────────────────────────────────────────
  http.sys (kernel):  accepts TCP connections → queues requests
  w3wp.exe (user):    CLR/.NET thread pool services requests

  .NET Thread Pool formulas (CLR-managed):
    maxWorkerThreads  = cpu_cores × 100   (handles CPU-bound + async work)
    maxIoThreads      = cpu_cores × 100   (handles IOCP completions)
    minWorkerThreads  = cpu_cores × 4     (pre-warmed — prevents ThreadPool starvation on startup)
    minIoThreads      = cpu_cores × 4

  IIS/http.sys queue:
    App Pool queue:    max(expected_concurrent × 2, 5000)
    http.sys kernel:   max(expected_concurrent × 4, 10000)

  Both queues are FIFO. When full, IIS returns 503.
  http.sys queue fills BEFORE App Pool queue — it is the first bottleneck.

Web Garden (maxProcesses > 1):
  max_processes = min(cpu_cores, app_pool_count_per_node)
  Web garden spawns multiple w3wp.exe per App Pool.
  Each w3wp.exe has its own thread pool → total thread capacity × max_processes.
  Downside: in-process session state (InProc) is NOT shared across workers.
  Use only with: StateServer, SQL session, or ASP.NET Core (stateless).

App Pool recycling:
  recycle_minutes = 1740 (29h — default, staggered from midnight)
  Private memory limit = RAM_per_pool × 70% in KB
  RAM_per_pool = (RAM_GB × 1024 × 0.80) / app_pool_count

Connection timeout:
  connectionTimeout = 30s (default 120s — holds http.sys resources)

Header wait timeout:
  headerWaitTimeout = 15s (default 120s — slow-header DoS attack surface)
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.iis import IISInput, IISOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class IISCalculator(BaseCalculator):

    def __init__(self, inp: IISInput) -> None:
        self._require_positive(inp.cpu_cores,           "cpu_cores")
        self._require_positive(inp.ram_gb,              "ram_gb")
        self._require_positive(inp.expected_concurrent, "expected_concurrent")
        self.inp = inp

    # ── core calculations ─────────────────────────────────────────────────────

    def _max_worker_threads(self) -> int:
        """CLR thread pool: cpu_cores × 100, min 400."""
        return max(400, self.inp.cpu_cores * 100)

    def _max_io_threads(self) -> int:
        """IOCP threads: cpu_cores × 100, min 400."""
        return max(400, self.inp.cpu_cores * 100)

    def _queue_length(self) -> int:
        """App Pool request queue: max(expected_concurrent × 2, 5000)."""
        return max(self.inp.expected_concurrent * 2, 5000)

    def _kernel_queue_length(self) -> int:
        """http.sys kernel queue: max(expected_concurrent × 4, 10000)."""
        return max(self.inp.expected_concurrent * 4, 10_000)

    def _recycle_minutes(self) -> int:
        """
        Recycle at 1740 min (29h) by default.
        Offset from default 1740 to avoid all pools recycling at midnight simultaneously.
        """
        return 1740

    def _max_processes(self) -> int:
        """Web garden: min(cpu_cores, 4) if enabled, else 1."""
        if not self.inp.web_garden:
            return 1
        return min(self.inp.cpu_cores, 4)

    def _private_memory_limit_kb(self) -> int:
        """
        App Pool private memory limit in KB.
        = (RAM × 80%) / app_pool_count × 70% safety margin.
        Expressed in KB (IIS applicationHost.config unit).
        """
        ram_per_pool_gb = (self.inp.ram_gb * 0.80) / self.inp.app_pool_count
        limit_gb = ram_per_pool_gb * 0.70
        return int(limit_gb * 1024 * 1024)  # GB → KB

    # ── Windows registry / netsh tuning block ─────────────────────────────────

    def _windows_tuning_block(self) -> str:
        inp   = self.inp
        kql   = self._kernel_queue_length()

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX IIS Windows Tuning  [{inp.mode.value.upper():8s}]  "
            f"cores={inp.cpu_cores}  RAM={inp.ram_gb}GB  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"# ── Run as Administrator in PowerShell ──────────────────────────

"
            f"# 1. http.sys kernel-mode request queue depth
"
            f"#    (default 1000 — silently drops at 1001st concurrent request)
"
            f"netsh http set serviceiplistenvalue ipaddress=0.0.0.0 `
"
            f"      queuelength={kql}

"
            f"# 2. TCP tuning
"
            f"netsh int tcp set global autotuninglevel=normal
"
            f"netsh int tcp set global chimney=disabled
"
            f"netsh int tcp set global rss=enabled
"
            f"netsh int tcp set global fastopen=enabled

"
            f"# 3. Nagle algorithm — disable for low-latency APIs
"
            f"Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' `
"
            f"  -Name 'TcpAckFrequency' -Value 1 -Type DWord
"
            f"Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' `
"
            f"  -Name 'TCPNoDelay' -Value 1 -Type DWord

"
            f"# 4. Ephemeral port range — default 49152-65535 (16384 ports)
"
            f"#    Expand to allow more simultaneous outbound connections
"
            f"netsh int ipv4 set dynamicport tcp start=10000 num=55535

"
            f"# 5. TIME_WAIT reduction (2MSL = 4 minutes default)
"
            f"Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' `
"
            f"  -Name 'TcpTimedWaitDelay' -Value 30 -Type DWord

"
            f"# 6. IIS kernel-mode output cache (if enabled)
"
            + (
                f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
                f"  -filter 'system.webServer/caching' -name 'enabled' -value True
"
                f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
                f"  -filter 'system.webServer/caching' -name 'enableKernelCache' -value True

"
                if inp.output_cache_enabled else
                f"# output_cache_enabled=False: kernel cache disabled

"
            ) +
            f"# 7. TLS hardening (disable TLS 1.0, 1.1 via registry)
"
            f"$tls10path = 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server'
"
            f"New-Item -Path $tls10path -Force | Out-Null
"
            f"Set-ItemProperty -Path $tls10path -Name 'Enabled' -Value 0 -Type DWord
"
            f"Set-ItemProperty -Path $tls10path -Name 'DisabledByDefault' -Value 1 -Type DWord
"
            f"$tls11path = 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.1\Server'
"
            f"New-Item -Path $tls11path -Force | Out-Null
"
            f"Set-ItemProperty -Path $tls11path -Name 'Enabled' -Value 0 -Type DWord
"
            f"Set-ItemProperty -Path $tls11path -Name 'DisabledByDefault' -Value 1 -Type DWord

"
            f"# 8. Crypto: prefer ECDHE + AES-GCM (IISCrypto tool recommended)
"
            f"# Download: https://www.nartac.com/Products/IISCrypto
"
            f"# Or use: https://github.com/MicrosoftDocs/iis-docs cipher order groups
"
        )

    # ── applicationHost.config snippet ───────────────────────────────────────

    def _render_apphost_config(self, mwt: int, mit: int, ql: int, kql: int,
                                recycle: int, procs: int, mem_kb: int) -> str:
        inp = self.inp

        http2_attr = 'http2Enabled="true"' if inp.http2_enabled else 'http2Enabled="false"'

        return (
            f"<!-- ╔══════════════════════════════════════════════════════════════╗ -->
"
            f"<!-- ║  VAREX IIS applicationHost.config  [{inp.mode.value.upper():8s}]  "
            f"IIS10  .NET={inp.dotnet_version}  ║ -->
"
            f"<!-- ╚══════════════════════════════════════════════════════════════╝ -->

"
            f"<!-- Location: %SystemRoot%\System32\inetsrv\config\applicationHost.config -->

"
            f'<system.applicationHost>

'
            f'    <!-- ── App Pool ─────────────────────────────────────────────── -->
'
            f'    <applicationPools>
'
            f'        <add name="DefaultAppPool"
'
            f'             managedRuntimeVersion="{inp.dotnet_version if inp.dotnet_version != "none" else ""}"
'
            f'             managedPipelineMode="{inp.managed_pipeline_mode}"
'
            f'             startMode="AlwaysRunning">
'
            f'            <processModel
'
            f'                maxProcesses="{procs}"
'
            f'                idleTimeout="00:00:00"
'
            f'                idleTimeoutAction="Terminate"
'
            f'                maxWorkerThreads="{mwt}"
'
            f'                maxIoThreads="{mit}"
'
            f'                minWorkerThreads="{max(4, inp.cpu_cores * 4)}"
'
            f'                minIoThreads="{max(4, inp.cpu_cores * 4)}"
'
            f'                shutdownTimeLimit="00:01:30"
'
            f'                startupTimeLimit="00:01:30"
'
            f'                pingEnabled="true"
'
            f'                pingInterval="00:00:30"
'
            f'                pingResponseTime="00:01:30"/>
'
            f'            <recycling>
'
            f'                <periodicRestart
'
            f'                    time="{recycle // 60:02d}:{recycle % 60:02d}:00"
'
            f'                    privateMemory="{mem_kb}"
'
            f'                    requests="0">
'
            f'                    <schedule>
'
            f'                        <!-- Stagger recycle times across App Pools -->
'
            f'                        <add value="03:00:00"/>
'
            f'                    </schedule>
'
            f'                </periodicRestart>
'
            f'                <logEventOnRecycle>Memory, PrivateMemory, Requests, Time, Schedule</logEventOnRecycle>
'
            f'            </recycling>
'
            f'            <failure
'
            f'                rapidFailProtection="true"
'
            f'                rapidFailProtectionInterval="00:05:00"
'
            f'                rapidFailProtectionMaxCrashes="5"
'
            f'                autoShutdownExe=""
'
            f'                orphanWorkerProcess="false"/>
'
            f'            <limits
'
            f'                requestQueueLength="{ql}"
'
            f'                requestQueueDelegatorIdentity=""/>
'
            f'        </add>
'
            f'    </applicationPools>

'
            f'    <!-- ── Site / Connections ────────────────────────────────────── -->
'
            f'    <sites>
'
            f'        <siteDefaults>
'
            f'            <limits
'
            f'                maxConnections="4294967295"
'
            f'                connectionTimeout="00:00:30"
'
            f'                headerWaitTimeout="00:00:15"
'
            f'                minBytesPerSecond="240"/>
'
            f'        </siteDefaults>
'
            f'    </sites>

'
            f'    <!-- ── HTTP Protocol ─────────────────────────────────────────── -->
'
            f'    <webLimits
'
            f'        connectionTimeout="00:00:30"
'
            f'        headerWaitTimeout="00:00:15"
'
            f'        minBytesPerSecond="240"
'
            f'        maxGlobalBandwidth="4294967295"/>

'
            f'</system.applicationHost>

'
            f'<!-- ── system.webServer ──────────────────────────────────────────── -->
'
            f'<system.webServer>
'
            f'    <serverRuntime
'
            f'        enabled="true"
'
            f'        frequentHitThreshold="2"
'
            f'        frequentHitTimePeriod="00:00:10"
'
            f'        maxRequestEntityAllowed="1073741824"
'
            f'        uploadReadAheadSize="49152"/>

'
            f'    <httpProtocol>
'
            f'        <customHeaders>
'
            f'            <remove name="X-Powered-By"/>
'
            f'        </customHeaders>
'
            f'    </httpProtocol>

'
            f'    <security>
'
            f'        <requestFiltering>
'
            f'            <requestLimits
'
            f'                maxAllowedContentLength="1073741824"
'
            f'                maxUrl="16384"
'
            f'                maxQueryString="16384"/>
'
            f'        </requestFiltering>
'
            f'    </security>

'
            f'    <caching
'
            f'        enabled="{str(inp.output_cache_enabled).lower()}"
'
            f'        enableKernelCache="{str(inp.output_cache_enabled).lower()}"/>

'
            f'    <httpCompression
'
            f'        directory="%SystemDrive%\inetpub\temp\IIS Temporary Compressed Files"
'
            f'        doDynamicCompression="true"
'
            f'        doStaticCompression="true"
'
            f'        staticCompressionLevel="7">
'
            f'        <scheme name="gzip" dll="%Windir%\system32\inetsrv\gzip.dll"/>
'
            f'        <dynamicTypes>
'
            f'            <add mimeType="text/*"        enabled="true"/>
'
            f'            <add mimeType="message/*"     enabled="true"/>
'
            f'            <add mimeType="application/json" enabled="true"/>
'
            f'            <add mimeType="application/javascript" enabled="true"/>
'
            f'            <add mimeType="*/*"           enabled="false"/>
'
            f'        </dynamicTypes>
'
            f'    </httpCompression>

'
            f'</system.webServer>
'
        )

    # ── PowerShell snippet ────────────────────────────────────────────────────

    def _render_powershell(self, mwt: int, mit: int, ql: int, recycle: int,
                            procs: int, mem_kb: int) -> str:
        inp = self.inp
        min_t = max(4, inp.cpu_cores * 4)

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX IIS PowerShell Config  [{inp.mode.value.upper():8s}]  "
            f".NET={inp.dotnet_version}  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Run as Administrator. Requires WebAdministration module.
"
            f"Import-Module WebAdministration

"
            f"$pool = 'DefaultAppPool'

"
            f"# ── App Pool runtime ──────────────────────────────────────────
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.maxWorkerThreads {mwt}
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.maxIoThreads {mit}
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.minWorkerThreads {min_t}
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.minIoThreads {min_t}
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.maxProcesses {procs}
"
            f"Set-ItemProperty IIS:\AppPools\$pool processModel.idleTimeout '00:00:00'
"
            f"Set-ItemProperty IIS:\AppPools\$pool startMode 'AlwaysRunning'

"
            f"# ── Recycling ─────────────────────────────────────────────────
"
            f"Set-ItemProperty IIS:\AppPools\$pool recycling.periodicRestart.time `
"
            f"  '{recycle // 60:02d}:{recycle % 60:02d}:00'
"
            f"Set-ItemProperty IIS:\AppPools\$pool `
"
            f"  recycling.periodicRestart.privateMemory {mem_kb}
"
            f"Set-ItemProperty IIS:\AppPools\$pool `
"
            f"  recycling.periodicRestart.requests 0

"
            f"# ── Request queue ─────────────────────────────────────────────
"
            f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter "system.applicationHost/applicationPools/add[@name='$pool']/limits" `
"
            f"  -name 'requestQueueLength' -value {ql}

"
            f"# ── Site limits ───────────────────────────────────────────────
"
            f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter 'system.applicationHost/sites/siteDefaults/limits' `
"
            f"  -name 'connectionTimeout' -value '00:00:30'
"
            f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter 'system.applicationHost/sites/siteDefaults/limits' `
"
            f"  -name 'headerWaitTimeout' -value '00:00:15'

"
            f"# ── HTTP/2 ────────────────────────────────────────────────────
"
            + (
                "Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
                "  -filter 'system.webServer/serverRuntime' `
"
                "  -name 'enabled' -value True

"
                if inp.http2_enabled else
                "# http2_enabled=False: HTTP/2 disabled

"
            ) +
            f"# ── Remove X-Powered-By header ────────────────────────────────
"
            f"Remove-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter 'system.webServer/httpProtocol/customHeaders' `
"
            f"  -name '.' -AtElement @{{name='X-Powered-By'}}

"
            f"# ── Compression ───────────────────────────────────────────────
"
            f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter 'system.webServer/httpCompression' `
"
            f"  -name 'doDynamicCompression' -value True
"
            f"Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
"
            f"  -filter 'system.webServer/httpCompression' `
"
            f"  -name 'doStaticCompression' -value True
"
        )

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, mwt: int, mit: int, ql: int, kql: int,
                      recycle: int, procs: int, mem_kb: int) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        min_t = max(4, inp.cpu_cores * 4)
        mem_gb = round(mem_kb / 1024 / 1024, 2)

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "maxWorkerThreads", str(mwt), M,
                f"CLR thread pool worker threads = {mwt} = cpu_cores({inp.cpu_cores}) × 100. "
                "IIS default = 25 per CPU — catastrophically low for modern web apps. "
                "Each async I/O operation (DB query, HTTP call) parks a thread in IOCP; "
                f"with 25 max threads, {25 * inp.cpu_cores} concurrent requests = thread starvation. "
                "At {mwt}: {inp.cpu_cores} cores × 100 threads = "
                f"{mwt} simultaneous synchronous operations. "
                "ASP.NET Core runs async — actual concurrent requests >> thread count. "
                "Too high: context switching overhead. Formula is safe upper bound.",
                f"processModel maxWorkerThreads={mwt}",
                str(ex.max_worker_threads) if ex.max_worker_threads else None,
                safe=False,
            ),
            p(
                "maxIoThreads", str(mit), M,
                f"IOCP completion threads = {mit} = cpu_cores({inp.cpu_cores}) × 100. "
                "IOCP threads handle async I/O callbacks (network, disk). "
                "Undersized IOCP threads: async operations complete but callback "
                "waits for an IOCP thread — latency spike invisible in CPU metrics. "
                "Default 25: starves on any I/O-heavy workload.",
                f"processModel maxIoThreads={mit}",
                str(ex.max_io_threads) if ex.max_io_threads else None,
                safe=False,
            ),
            p(
                "requestQueueLength (App Pool)", str(ql), M,
                f"App Pool request queue depth = {ql} = max(expected_concurrent×2, 5000). "
                "Requests beyond this queue return 503.3 Service Unavailable. "
                "This is the SECOND queue (after http.sys kernel queue). "
                "Monitor: Performance Monitor → W3SVC_W3WP\Requests Queued.",
                f"limits requestQueueLength={ql}",
                str(ex.queue_length) if ex.queue_length else None,
                safe=False,
            ),
            p(
                "http.sys kernel queue", str(kql), M,
                f"http.sys kernel-mode request queue = {kql} = max(expected_concurrent×4, 10000). "
                "This is the FIRST queue (before App Pool). "
                "When full: http.sys returns 503 in kernel mode — fastest possible 503 "
                "but also first to fill under traffic spike. "
                "Set via: netsh http set serviceiplistenvalue. "
                "Default 1000 — exhausted at 1001 concurrent requests.",
                f"netsh http set serviceiplistenvalue ... queuelength={kql}",
                str(ex.kernel_queue_length) if ex.kernel_queue_length else None,
                safe=False,
            ),
            p(
                "managed pipeline mode", inp.managed_pipeline_mode, M,
                {
                    "Integrated": (
                        "Integrated mode: IIS and ASP.NET share a unified request pipeline. "
                        "IIS modules (authentication, URL rewrite, compression) participate "
                        "in the same pipeline as .NET HttpModules. "
                        "Required for: ASP.NET Core, MVC, Web API. "
                        "Performance: 10–30% faster than Classic (no COM interop boundary)."
                    ),
                    "Classic": (
                        "Classic mode: legacy ISAPI pipeline. "
                        "Required only for: classic ASP, old ISAPI extensions. "
                        ".NET requests processed via ISAPI bridge — performance penalty. "
                        "NEVER use Classic for new .NET Framework 4.x or .NET Core apps. "
                        "Migrate to Integrated mode."
                    ),
                }.get(inp.managed_pipeline_mode, ""),
                f'managedPipelineMode="{inp.managed_pipeline_mode}"',
                ex.managed_pipeline_mode,
                safe=False,
            ),
            p(
                "startMode", "AlwaysRunning", M,
                "Default 'OnDemand': App Pool starts on first request — "
                "causes cold-start latency (JIT + app init = 2–30s for .NET apps). "
                "AlwaysRunning: w3wp.exe starts with IIS, app pre-warmed. "
                "Zero cold-start on first request. "
                "Requires Application Initialization module (IIS 8.0+). "
                "Essential for production .NET apps behind load balancers.",
                'startMode="AlwaysRunning"',
                safe=False,
            ),
            p(
                "privateMemory recycling", f"{mem_kb:,} KB ({mem_gb} GB)", M,
                f"App Pool private memory limit = {mem_kb:,} KB ({mem_gb} GB). "
                f"Formula: (RAM({inp.ram_gb}GB) × 80% / app_pools({inp.app_pool_count})) × 70% = {mem_gb}GB. "
                "When w3wp.exe exceeds this: App Pool recycles (restart). "
                "Without this: memory leaks in .NET apps grow unbounded until host OOM. "
                "Set lower than available RAM/pool to ensure graceful recycle before OOM kill. "
                "Monitor: Performance Monitor → Process\Private Bytes (w3wp).",
                f"recycling.periodicRestart.privateMemory={mem_kb}",
                safe=False,
            ),

            # ── MEDIUM: connection / timeout / security ───────────────────
            p(
                "connectionTimeout", "30s", MED,
                "Default 120s — http.sys holds a connection handle for 2 minutes. "
                "At 1000 slow clients: 1000 handles × 120s = 2 minutes of waste. "
                "30s: 4× faster handle reclamation. "
                "Increase to 60s for large file upload endpoints.",
                'connectionTimeout="00:00:30"',
                str(ex.connection_timeout) if ex.connection_timeout else None,
            ),
            p(
                "headerWaitTimeout", "15s", MED,
                "Default 120s — time http.sys waits for complete HTTP headers after TCP connect. "
                "Slowloris attack: attacker opens connections and sends headers 1 byte/second. "
                "At 120s: attacker holds 1 thread per connection for 2 minutes. "
                "15s: limits Slowloris exposure 8×. "
                "Cannot be below 5s (breaks some legacy HTTP clients).",
                'headerWaitTimeout="00:00:15"',
                str(ex.header_wait_timeout) if ex.header_wait_timeout else None,
            ),
            p(
                "idleTimeout", "Disabled (00:00:00)", MED,
                "Default 20 minutes: IIS shuts down w3wp.exe after 20min idle. "
                "Next request after idle: full cold-start latency again. "
                "Set to 0 (disabled) for production servers with startMode=AlwaysRunning. "
                "Idle shutdown makes sense only for dev/staging to save RAM.",
                'processModel idleTimeout="00:00:00"',
                str(ex.idle_timeout) if ex.idle_timeout else None,
            ),
            p(
                "periodicRestart (time)", f"{recycle // 60:02d}:{recycle % 60:02d}", MED,
                f"App Pool time-based recycle = {recycle // 60}h{recycle % 60}m (29 hours). "
                "Default 1740 min (29h) — avoids midnight simultaneous recycle. "
                "Recycling restarts w3wp.exe to clear .NET heap fragmentation, "
                "connection pool leaks, native memory leaks. "
                "Set a specific time (03:00) to control recycle window. "
                "With privateMemory limit: recycle happens earlier if memory threshold hit.",
                'periodicRestart time="29:00:00" / schedule add value="03:00:00"',
                str(ex.recycle_minutes) if ex.recycle_minutes else None,
            ),
            p(
                "minWorkerThreads / minIoThreads", f"{min_t} / {min_t}", MED,
                f"Pre-created CLR thread pool threads = {min_t} = cpu_cores({inp.cpu_cores}) × 4. "
                "Without pre-created threads: .NET ThreadPool creates 1 thread/500ms on burst "
                "(ThreadPool injection rate limit). "
                f"At {inp.expected_concurrent} concurrent requests burst: "
                f"ThreadPool needs {inp.expected_concurrent} threads — takes "
                f"{max(0, inp.expected_concurrent - inp.cpu_cores) // 2}s to inject. "
                "Requests queue during injection = latency spike. "
                f"Pre-create {min_t} threads: burst up to {min_t} handled instantly.",
                f"processModel minWorkerThreads={min_t} minIoThreads={min_t}",
            ),
            p(
                "maxProcesses (Web Garden)", str(procs), MED,
                f"w3wp.exe processes per App Pool = {procs}. "
                + (
                    f"Web garden enabled: {procs} processes × {mwt} threads = "
                    f"{procs * mwt} total threads. "
                    "Each process has independent CLR heap — no lock contention. "
                    "WARNING: InProc session state NOT shared across processes. "
                    "Use only with: SQL/Redis session, ASP.NET Core (stateless)."
                    if inp.web_garden else
                    "Single process (web garden disabled). "
                    "Simpler debugging, all memory in one w3wp.exe. "
                    f"Enable web garden if CPU utilisation on {inp.cpu_cores} cores < 50%."
                ),
                f"processModel maxProcesses={procs}",
                str(ex.max_processes) if ex.max_processes else None,
            ),
            p(
                "HTTP/2", "enabled", MED,
                "IIS 10 (Windows Server 2016+) supports HTTP/2 natively. "
                "HTTP/2 multiplexes multiple requests over 1 TLS connection — "
                "eliminates head-of-line blocking for browser clients. "
                "Requires HTTPS. "
                "ASP.NET Core: HTTP/2 + gRPC requires HTTP/2 cleartext (h2c) for inter-service. "
                "Disable only for: legacy Java/Python clients that reject HTTP/2 upgrades.",
                'http2Enabled="true" (via netsh + IIS Manager)',
            ) if inp.http2_enabled else None,
            p(
                "Dynamic + Static compression", "enabled", MED,
                "doDynamicCompression + doStaticCompression. "
                "Compresses JSON/HTML/JS/CSS by 60–80%. "
                "Dynamic compression CPU cost: < 1% for modern GZIP on IIS. "
                "kernel-mode output cache + static compression = cached compressed responses "
                "served entirely from kernel — zero user-mode transition.",
                'httpCompression doDynamicCompression="true" doStaticCompression="true"',
            ),
            p(
                "Kernel-mode output cache", "enabled", MED,
                "IIS kernel output cache: http.sys serves cached responses "
                "without invoking w3wp.exe at all. "
                "frequentHitThreshold=2: cache after 2 identical requests in 10s. "
                "For static assets and low-churn API responses: 10–100× throughput increase. "
                "Cache stored in non-paged pool — does not consume process virtual memory.",
                'caching enabled="true" enableKernelCache="true"
'
                'serverRuntime frequentHitThreshold="2" frequentHitTimePeriod="00:00:10"',
            ) if inp.output_cache_enabled else None,
        ]

        if inp.reverse_proxy:
            params += [
                p(
                    "ARR (Application Request Routing)", "enabled", MED,
                    "ARR + URL Rewrite: IIS as reverse proxy. "
                    "ARR health checks remove unhealthy backends automatically. "
                    "ARR disk offload: proxy large response bodies via temp files "
                    "to prevent w3wp.exe memory pressure on large payloads. "
                    "ARR server farm: defines backend pool with weights + health probes.",
                    "# Install ARR from WebPI or Chocolatey:
"
                    "# choco install iis-arr
"
                    "# Configure via IIS Manager → Server Farms",
                ),
            ]

        params += [
            p(
                "Remove X-Powered-By", "enabled", MIN,
                "IIS default sends 'X-Powered-By: ASP.NET' header. "
                "Reveals .NET version to attackers. Remove via customHeaders.",
                "<remove name='X-Powered-By'/>",
            ),
            p(
                "rapidFailProtection", "true / 5 crashes in 5 min", MIN,
                "Rapid fail protection: if App Pool crashes 5 times in 5 minutes, "
                "IIS stops the App Pool and returns 503. "
                "Prevents crash-restart loop from consuming CPU. "
                "Configure alert when App Pool stops: Event Log ID 5002.",
                'failure rapidFailProtection="true" rapidFailProtectionMaxCrashes="5"',
            ),
            p(
                "logEventOnRecycle", "all events", MIN,
                "Log recycle reason to Windows Event Log. "
                "Default: only logs time-based recycles. "
                "Set ALL causes: Memory, PrivateMemory, Requests, Time, Schedule. "
                "Essential for understanding why w3wp.exe is recycling in production.",
                'logEventOnRecycle="Memory, PrivateMemory, Requests, Time, Schedule"',
            ),
            p(
                "TLS hardening (SCHANNEL registry)", "TLS 1.2/1.3 only", MIN,
                "IIS TLS is controlled by Windows SCHANNEL registry keys, "
                "NOT by IIS config files. "
                "Disable TLS 1.0, 1.1, SSL 3.0 via registry + reboot. "
                "Use IISCrypto (Nartac) GUI tool for safe cipher suite management. "
                "CIS Benchmark for IIS 10 requires: TLS 1.2+, no RC4, no 3DES.",
                "# See PowerShell block for SCHANNEL registry commands",
            ),
            p(
                "Request filtering limits", "maxUrl=16384, maxQueryString=16384", MIN,
                "Default maxUrl=260 — too short for long REST API paths. "
                "Default maxQueryString=2048 — too short for complex filter params. "
                "Increase to 16384 for modern REST APIs.",
                'requestLimits maxUrl="16384" maxQueryString="16384"',
                safe=False,
            ),
        ]

        return [x for x in params if x is not None]

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, mwt: int, mit: int, ql: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.max_worker_threads and ex.max_worker_threads <= 25:
            findings.append(
                f"[MAJOR] maxWorkerThreads={ex.max_worker_threads} — IIS install default. "
                f"Severely undersized for {self.inp.cpu_cores} cores. "
                f"Recommended: {mwt}. Thread starvation likely under any I/O-bound load."
            )
        if ex.max_io_threads and ex.max_io_threads <= 25:
            findings.append(
                f"[MAJOR] maxIoThreads={ex.max_io_threads} — IIS install default. "
                f"IOCP completion callbacks will queue. Recommended: {mit}."
            )
        if ex.queue_length and ex.queue_length < 5000:
            findings.append(
                f"[MEDIUM] requestQueueLength={ex.queue_length}. "
                f"Too low — 503.3 under modest traffic spike. Recommended: {ql}."
            )
        if ex.kernel_queue_length and ex.kernel_queue_length < 5000:
            findings.append(
                f"[MAJOR] http.sys kernel queue={ex.kernel_queue_length}. "
                "http.sys silently drops connections beyond this. "
                f"Recommended: {self._kernel_queue_length()}. "
                "Set via: netsh http set serviceiplistenvalue ... queuelength=<N>"
            )
        if ex.managed_pipeline_mode == "Classic":
            findings.append(
                "[MAJOR] managedPipelineMode=Classic. "
                "Legacy ISAPI pipeline. 10–30% slower than Integrated. "
                "Switch to Integrated unless Classic ASP / old ISAPI required."
            )
        if ex.idle_timeout and ex.idle_timeout > 0:
            findings.append(
                f"[MEDIUM] idleTimeout={ex.idle_timeout}min. "
                "w3wp.exe shuts down after idle — cold start on next request. "
                "Set to 0 for production. Use startMode=AlwaysRunning."
            )
        if ex.connection_timeout and ex.connection_timeout > 60:
            findings.append(
                f"[MEDIUM] connectionTimeout={ex.connection_timeout}s. "
                "http.sys holds handles for {ex.connection_timeout}s. Reduce to 30s."
            )
        if ex.header_wait_timeout and ex.header_wait_timeout > 30:
            findings.append(
                f"[MEDIUM] headerWaitTimeout={ex.header_wait_timeout}s. "
                "Slowloris DoS attack surface. Reduce to 15s."
            )
        if ex.output_cache_enabled is False and self.inp.output_cache_enabled:
            findings.append(
                "[MEDIUM] Kernel-mode output cache disabled. "
                "Enable for static assets + low-churn API responses."
            )
        if ex.tls_protocols:
            for weak in ("TLS 1.0", "TLS 1.1", "SSL 3", "SSL 2"):
                if weak in ex.tls_protocols:
                    findings.append(
                        f"[MAJOR] TLS protocol '{weak}' enabled. "
                        "Disable via SCHANNEL registry. CIS IIS Benchmark requires TLS 1.2+."
                    )

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> IISOutput:
        mwt      = self._max_worker_threads()
        mit      = self._max_io_threads()
        ql       = self._queue_length()
        kql      = self._kernel_queue_length()
        recycle  = self._recycle_minutes()
        procs    = self._max_processes()
        mem_kb   = self._private_memory_limit_kb()

        all_params = self._build_params(mwt, mit, ql, kql, recycle, procs, mem_kb)

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = ql,
            os_type   = self.inp.os_type,
            existing  = {},
        )

        major, medium, minor = self._split(all_params)

        return IISOutput(
            mode                    = self.inp.mode,
            max_worker_threads      = mwt,
            max_io_threads          = mit,
            queue_length            = ql,
            kernel_queue_length     = kql,
            recycle_minutes         = recycle,
            max_processes           = procs,
            private_memory_limit_kb = mem_kb,
            apphostconfig_snippet   = self._render_apphost_config(
                                        mwt, mit, ql, kql, recycle, procs, mem_kb),
            powershell_snippet      = self._render_powershell(
                                        mwt, mit, ql, recycle, procs, mem_kb),
            major_params            = major,
            medium_params           = medium,
            minor_params            = minor,
            os_sysctl_conf          = self._windows_tuning_block(),
            ha_suggestions=[
                "Use Windows Network Load Balancing (NLB) or ARR server farm for IIS HA.",
                "ASP.NET session: use SQL Server session or Redis (StackExchange.Redis) "
                "— never InProc when running multiple IIS nodes.",
                "Deploy behind Azure Application Gateway or AWS ALB for SSL offload + WAF.",
                "Use Application Initialization module + warmup URLs to pre-heat "
                "App Pool after recycle before LB health check passes.",
                "Web Deploy (MSDeploy) for zero-downtime deployments: "
                "deploy to one node at a time while LB serves others.",
                "Enable Failed Request Tracing (FREB) on staging — never production "
                "(high I/O overhead per request).",
            ],
            performance_warnings=[w for w in [
                ("managedPipelineMode=Classic selected. "
                 "10–30% slower than Integrated. Migrate unless ISAPI required.")
                if self.inp.managed_pipeline_mode == "Classic" else None,
                ("web_garden=True with dotnet_version=v4.0: verify session mode. "
                 "InProc session will NOT be shared across w3wp processes.")
                if self.inp.web_garden and self.inp.dotnet_version == "v4.0" else None,
                ("http2_enabled=False: HTTP/2 multiplexing disabled. "
                 "Browser clients make sequential requests on each connection.")
                if not self.inp.http2_enabled else None,
                ("idle_timeout default (20min) will cause cold starts. "
                 "Ensure startMode=AlwaysRunning is set.")
                if self.inp.existing.idle_timeout and self.inp.existing.idle_timeout > 0 else None,
            ] if w],
            capacity_warning        = self._capacity_warning(
                self.inp.expected_concurrent, ql, "IIS App Pool queue"
            ),
            audit_findings          = self._audit(mwt, mit, ql)
                                      if self.inp.mode == CalcMode.EXISTING else [],
        )
