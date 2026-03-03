"""
app/calculators/tomcat_calculator.py
=====================================
Tomcat tuning calculator — NEW and EXISTING modes.

Thread count formula (Brian Goetz — Java Concurrency in Practice)
-----------------------------------------------------------------
N = U * C * (1 + W / C)

Where:
  N = optimal thread count
  U = target CPU utilisation (0.0–1.0), default 0.90
  C = cpu_cores
  W = avg_response_ms (total request time)
  C_time = avg_response_ms * (1 - io_wait_ratio)  (CPU time per request)

Simplified: N = ceil(U * cpu_cores * (1 + io_wait_ratio / (1 - io_wait_ratio)))

Applied clamp: max(50, min(N, 1000))
  - Floor 50: minimum viable thread pool (prevents Tomcat starvation on tiny inputs)
  - Ceiling 1000: JVM overhead per thread ~1MB stack; 1000 threads = ~1GB stack RAM

JVM heap formula
----------------
xmx_gb = RAM * heap_ratio
xms_gb = xmx_gb   (equal Xms=Xmx eliminates GC-triggered heap resize pauses)
metaspace_mb = 512 + (cpu_cores * 32)  (class metadata grows with framework usage)
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.tomcat import TomcatInput, TomcatOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR

_TARGET_CPU_UTIL = 0.90   # Goetz U — target 90% CPU utilisation


class TomcatCalculator(BaseCalculator):

    def __init__(self, inp: TomcatInput) -> None:
        self._require_positive(inp.cpu_cores,          "cpu_cores")
        self._require_positive(inp.ram_gb,             "ram_gb")
        self._require_positive(inp.target_concurrency, "target_concurrency")
        self._require_positive(inp.avg_response_ms,    "avg_response_ms")
        self._require_range(inp.io_wait_ratio, 0.01, 0.99, "io_wait_ratio")
        self.inp = inp

    # ── Goetz thread formula ──────────────────────────────────────────────────

    def _goetz_threads(self) -> int:
        """
        Goetz optimal thread count.
        N = U * C * (1 + W/C_time)
          = U * C * (1 + io_wait_ratio / (1 - io_wait_ratio))
        """
        C = self.inp.cpu_cores
        W_ratio = self.inp.io_wait_ratio
        C_ratio = 1.0 - W_ratio           # CPU fraction of request time
        N = _TARGET_CPU_UTIL * C * (1 + W_ratio / C_ratio)
        return max(50, min(math.ceil(N), 1000))

    def _goetz_trace(self, N: int) -> str:
        C = self.inp.cpu_cores
        W = self.inp.avg_response_ms
        W_ratio = self.inp.io_wait_ratio
        C_ratio = 1.0 - W_ratio
        C_time  = round(W * C_ratio, 1)
        W_time  = round(W * W_ratio, 1)
        return (
            f"Goetz formula: N = U × C × (1 + W/C_time)
"
            f"  U (target CPU util) = {_TARGET_CPU_UTIL}
"
            f"  C (cpu_cores)       = {C}
"
            f"  W (avg_response_ms) = {W}ms
"
            f"  io_wait_ratio       = {W_ratio} → W_time={W_time}ms, C_time={C_time}ms
"
            f"  N = {_TARGET_CPU_UTIL} × {C} × (1 + {W_time}/{C_time})
"
            f"  N = {_TARGET_CPU_UTIL} × {C} × {round(1 + W_time/C_time, 3)}
"
            f"  N = {round(_TARGET_CPU_UTIL * C * (1 + W_time/C_time), 2)} "
            f"→ ceil = {N} (clamped to [50, 1000])"
        )

    # ── JVM heap ──────────────────────────────────────────────────────────────

    def _xmx_gb(self) -> float:
        return round(self.inp.ram_gb * self.inp.heap_ratio, 2)

    def _metaspace_mb(self) -> int:
        """
        512MB base + 32MB per core.
        Spring Boot / Jakarta EE apps load thousands of classes.
        Undersized MetaspaceSize causes repeated GC followed by java.lang.OutOfMemoryError: Metaspace.
        """
        return 512 + (self.inp.cpu_cores * 32)

    def _gc_threads(self) -> int:
        """
        GC thread count. Oracle recommended: min(cpu_cores, 8) + (cpu_cores - 8) * 5/8
        For <= 8 cores: equals cpu_cores. For > 8: grows sub-linearly.
        """
        C = self.inp.cpu_cores
        if C <= 8:
            return C
        return 8 + math.ceil((C - 8) * 5 / 8)

    def _min_spare_threads(self, max_t: int) -> int:
        return max(10, max_t // 10)

    def _accept_count(self, max_t: int) -> int:
        """
        Accept queue depth (TCP backlog for Tomcat's listen socket).
        Formula: max(200, max_threads // 2)
        Connections beyond acceptCount are rejected immediately (RST).
        """
        return max(200, max_t // 2)

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, max_t: int, xmx: float, meta: int, gc_t: int) -> list:
        ex    = self.inp.existing
        p     = self._p
        inp   = self.inp
        xms   = xmx
        mst   = self._min_spare_threads(max_t)
        ac    = self._accept_count(max_t)
        proto = f"org.apache.coyote.http11.Http11{'Nio2' if inp.connector_type == 'NIO2' else 'Nio' if inp.connector_type == 'NIO' else 'Apr'}Protocol"

        params = [

            # ── MAJOR: thread pool / heap ─────────────────────────────────
            p(
                "maxThreads", str(max_t), M,
                f"Optimal thread count via Goetz formula = {max_t}. "
                f"io_wait_ratio={inp.io_wait_ratio} means each thread is blocked on I/O "
                f"{inp.io_wait_ratio*100:.0f}% of the time. "
                f"More threads compensate so CPUs stay busy. "
                f"At maxThreads={max_t}, CPU util target = {_TARGET_CPU_UTIL*100:.0f}%. "
                "Too low: requests queue in acceptCount, then rejected (503). "
                "Too high: RAM exhausted by thread stacks (~1MB/thread on 64-bit JVM).",
                f'<Connector maxThreads="{max_t}" ... />',
                str(ex.max_threads) if ex.max_threads else None,
                safe=False,
            ),
            p(
                "minSpareThreads", str(mst), M,
                f"Pre-created idle threads = {mst} (= maxThreads ÷ 10). "
                "Without spare threads, a burst of concurrent requests must wait for "
                "new threads to be created — each thread creation takes 5–20ms on JVM. "
                f"At {mst} spare threads, bursts up to {mst} concurrent requests hit zero queue time.",
                f'<Connector minSpareThreads="{mst}" ... />',
                str(ex.min_spare_threads) if ex.min_spare_threads else None,
            ),
            p(
                "acceptCount", str(ac), M,
                f"TCP accept queue depth = {ac}. "
                "Connections arriving when all threads are busy queue here. "
                f"Formula: max(200, maxThreads÷2) = max(200, {max_t}÷2) = {ac}. "
                "Exceeding acceptCount: OS sends TCP RST — immediate connection refused. "
                "acceptCount is NOT a safety valve — it is a temporary burst buffer. "
                "Must be ≤ net.core.somaxconn (OS ceiling).",
                f'<Connector acceptCount="{ac}" ... />',
                str(ex.accept_count) if ex.accept_count else None,
            ),
            p(
                "connector protocol", proto, M,
                f"NIO (Non-blocking I/O): event-driven, handles keep-alive connections efficiently. "
                "HTTP/1.1 (BIO): one thread blocked per connection — NEVER use in production. "
                "NIO2 (Async I/O): kernel async completion ports, slightly lower thread overhead. "
                "APR: native library, best raw throughput but requires libtcnative. "
                f"Recommended: {inp.connector_type} → {proto}.",
                f'<Connector protocol="{proto}" ... />',
                ex.connector_protocol,
                safe=False,
            ),
            p(
                "-Xmx / -Xms", f"{xmx}g / {xms}g", M,
                f"-Xmx={xmx}g = RAM({inp.ram_gb}GB) × heap_ratio({inp.heap_ratio}) = {xmx}GB. "
                f"Setting -Xms = -Xmx = {xmx}g is critical: "
                "With Xms < Xmx, JVM starts with Xms and expands to Xmx. "
                "Every heap expansion triggers a full GC — causing stop-the-world pauses "
                "on startup and under load bursts. Equal Xms=Xmx: heap pre-allocated, "
                "zero resize pauses. Memory cost: OS sees full Xmx committed immediately. "
                f"Remaining {inp.ram_gb - xmx:.1f}GB reserved for: OS, Metaspace ({meta}MB), "
                "off-heap buffers, GC overhead.",
                f"JAVA_OPTS=-Xms{xmx}g -Xmx{xmx}g",
                f"Xms={ex.xms_gb}g/Xmx={ex.xmx_gb}g" if ex.xmx_gb else None,
                safe=False,
            ),
            p(
                "MaxMetaspaceSize", f"{meta}m", M,
                f"JVM class metadata ceiling = {meta}MB. "
                f"Formula: 512MB base + {inp.cpu_cores} cores × 32MB = {meta}MB. "
                "Metaspace grows with: Spring Boot (loads 10K+ classes), "
                "JSP compilation (each JSP = a class), hot deployment, classpath depth. "
                "Without MaxMetaspaceSize: Metaspace grows unbounded until host OOM. "
                "Symptom without this: 'java.lang.OutOfMemoryError: Metaspace' "
                "after hours of uptime due to class loading leaks.",
                f"-XX:MaxMetaspaceSize={meta}m -XX:MetaspaceSize={meta//2}m",
                f"{ex.metaspace_mb}m" if ex.metaspace_mb else None,
                safe=False,
            ),
            p(
                "GC type", f"-XX:+Use{inp.gc_type}", M,
                {
                    "G1GC": (
                        "G1GC (Garbage First): default Java 9+. Divides heap into equal regions, "
                        "collects regions with most garbage first (hence 'G1'). "
                        "Pause target: 200ms default. Throughput: 95%+ for most workloads. "
                        "Best for: heap 4GB–32GB, latency-sensitive web apps."
                    ),
                    "ZGC": (
                        "ZGC: concurrent, pause < 1ms regardless of heap size (Java 15+ production). "
                        "Performs all GC work concurrently with application threads. "
                        "Throughput: ~5–15% lower than G1 (concurrent work costs CPU). "
                        "Best for: large heaps (32GB+), ultra-low latency APIs (<5ms p99)."
                    ),
                    "Shenandoah": (
                        "Shenandoah: concurrent compaction, sub-millisecond pauses. "
                        "Available in OpenJDK 12+ and Red Hat builds. "
                        "Similar to ZGC in pause characteristics, "
                        "better throughput for smaller heaps (<16GB). "
                        "Best for: Red Hat / OpenJDK on RHEL/CentOS."
                    ),
                    "ParallelGC": (
                        "ParallelGC: multi-threaded stop-the-world GC. "
                        "Maximum throughput but pauses of 1–10s on large heaps. "
                        "Only for: batch processing, offline jobs. "
                        "NEVER for: web APIs, real-time applications."
                    ),
                }.get(inp.gc_type, ""),
                f"-XX:+Use{inp.gc_type}",
                ex.gc_type,
                safe=False,
            ),
            p(
                "ParallelGCThreads", str(gc_t), M,
                f"GC worker threads = {gc_t}. "
                f"Oracle formula: min(C,8) + ceil((C-8)×5/8) = {gc_t} for {inp.cpu_cores} cores. "
                "Sub-linear scaling prevents GC from consuming all CPUs during collection. "
                "Too high: GC threads starve application threads. "
                "Too low: GC pauses lengthen, triggering cascading OOM under load.",
                f"-XX:ParallelGCThreads={gc_t} -XX:ConcGCThreads={max(1, gc_t//4)}",
                safe=False,
            ),

            # ── MEDIUM: connector tuning ──────────────────────────────────
            p(
                "connectionTimeout", "20000", MED,
                "Connector connection timeout = 20,000ms (20s). Default 60,000ms (60s). "
                "A slow or dead client holds a Tomcat thread for 60s by default. "
                "At maxThreads={max_t}, 60s timeout × concurrent slow clients "
                "can exhaust all threads. 20s balances legit slow connections vs DoS.",
                f'<Connector connectionTimeout="20000" ... />',
                str(ex.connection_timeout) if ex.connection_timeout else None,
            ),
            p(
                "keepAliveTimeout", "15000", MED,
                "Idle keep-alive connection timeout = 15,000ms (15s). "
                "HTTP keep-alive: client reuses existing TCP connection for subsequent requests. "
                "Without timeout: idle connections hold Tomcat threads indefinitely. "
                "15s: frees thread after 15s of inactivity while allowing legitimate reuse.",
                f'<Connector keepAliveTimeout="15000" ... />',
                str(ex.keep_alive_timeout) if ex.keep_alive_timeout else None,
            ),
            p(
                "maxKeepAliveRequests", "200", MED,
                "Max requests per keep-alive connection. Default 100. "
                "200: reduces TCP handshake overhead for heavy API clients. "
                "High-volume clients reuse the same connection for 200 requests "
                "before Tomcat forces reconnection.",
                f'<Connector maxKeepAliveRequests="200" ... />',
                str(ex.max_keep_alive_requests) if ex.max_keep_alive_requests else None,
            ),
            p(
                "compression", "on", MED,
                "GZIP response compression. Reduces JSON/HTML payload by 60–80%. "
                "Tomcat CPU cost: <1% for typical API payloads on modern hardware. "
                "compressibleMimeType: target text, JSON, XML only. "
                "compressionMinSize 2048: skip compression for responses <2KB "
                "(compression overhead exceeds savings).",
                '<Connector compression="on"
'
                '           compressionMinSize="2048"
'
                '           compressibleMimeType="text/html,text/xml,text/plain,'
                'text/css,text/javascript,application/json,application/javascript" />',
                ex.compression,
            ) if inp.compression_enabled else None,
            p(
                "maxConnections", str(max_t * 10), MED,
                f"Max simultaneous TCP connections = {max_t*10}. "
                "Connections beyond this are accepted by OS (up to acceptCount) but "
                "queued — not rejected. Default 10000 is fine unless very high concurrency. "
                f"Formula: maxThreads × 10 = {max_t} × 10 = {max_t*10}.",
                f'<Connector maxConnections="{max_t * 10}" ... />',
                str(ex.max_connections) if ex.max_connections else None,
            ),
            p(
                "GC pause target", "200ms", MED,
                "G1GC pause time target. Default 200ms is reasonable for web workloads. "
                "100ms: G1 spends more CPU on concurrent GC work, slightly lower throughput. "
                "50ms or less: only achievable with small heaps (<4GB) or ZGC. "
                "Setting unrealistically low targets forces G1 to trigger more frequent "
                "but smaller GC cycles.",
                "-XX:MaxGCPauseMillis=200",
            ) if inp.gc_type == "G1GC" else None,
            p(
                "G1HeapRegionSize", "auto", MED,
                "G1 heap region size. Default: auto-calculated as heap/2048. "
                "For heaps > 8GB: manually set to 8m or 16m to reduce region count overhead. "
                f"At {xmx}GB heap: recommended = "
                f"{'8m' if xmx >= 8 else '4m' if xmx >= 4 else 'default'}.",
                f"-XX:G1HeapRegionSize={'8m' if xmx >= 8 else '4m' if xmx >= 4 else '0'}",
            ) if inp.gc_type == "G1GC" else None,
            p(
                "JVM OOM heap dump", "enabled", MED,
                "On OutOfMemoryError, dump heap to file. "
                "Without this: JVM crash with no diagnostic data. "
                "With this: complete heap snapshot for root-cause analysis. "
                "ExitOnOutOfMemoryError: kill the JVM immediately instead of limping "
                "(a partially-live OOM'd JVM serves errors until manually restarted).",
                f"-XX:+HeapDumpOnOutOfMemoryError
"
                f"-XX:HeapDumpPath=/var/log/tomcat/heapdump.hprof
"
                f"-XX:+ExitOnOutOfMemoryError",
            ),
            p(
                "JVM string deduplication", "enabled", MED,
                "String deduplication (G1GC/ZGC): identifies duplicate String objects "
                "and makes them share the same char[] array. "
                "REST APIs heavily use String for JSON keys, headers, enum values — "
                "30–50% of heap can be duplicate Strings. "
                "Typical heap reduction: 10–25%. Zero CPU cost at steady state.",
                "-XX:+UseStringDeduplication",
            ) if inp.gc_type in ("G1GC", "ZGC") else None,

            # ── MINOR: observability / hardening ─────────────────────────
            p(
                "GC logging", "enabled", MIN,
                "GC log is essential for: identifying long pause events, "
                "tuning GC thread count, confirming heap expansion behaviour. "
                "FileCount=5 + FileSize=20m: rolling 100MB of GC history (keep last 5 files). "
                "Overhead: <0.1% CPU.",
                f"-Xlog:gc*:file=/var/log/tomcat/gc.log:time,uptime:filecount=5,filesize=20m",
            ),
            p(
                "JMX / JMX Exporter", "enabled", MIN,
                "JMX: Java Management Extensions — exposes heap, threads, GC, classloader metrics. "
                "prometheus-jmx-exporter sidecar converts JMX to Prometheus format. "
                "Without this: zero visibility into heap usage before OOM.",
                "# Add to CATALINA_OPTS:
"
                "-Dcom.sun.management.jmxremote
"
                "-Dcom.sun.management.jmxremote.port=9010
"
                "-Dcom.sun.management.jmxremote.authenticate=false
"
                "-Dcom.sun.management.jmxremote.ssl=false
"
                "# Use prometheus-jmx-exporter for Grafana dashboards",
            ),
            p(
                "Tomcat access log valve", "enabled", MIN,
                "Log request URI, status code, response time, bytes sent. "
                "Essential for: identifying slow endpoints, 4xx/5xx spike detection. "
                "pattern=%h %t %r %s %b %D logs response time (%D in milliseconds).",
                '<Valve className="org.apache.catalina.valves.AccessLogValve"
'
                '       directory="logs"
'
                '       prefix="localhost_access_log"
'
                '       suffix=".txt"
'
                '       pattern="%h %t &quot;%r&quot; %s %b %D" />',
            ),
            p(
                "CATALINA_OPTS vs JAVA_OPTS", "CATALINA_OPTS", MIN,
                "Always set JVM flags in CATALINA_OPTS, not JAVA_OPTS. "
                "JAVA_OPTS applies to all Java processes including the Tomcat startup shell scripts. "
                "CATALINA_OPTS applies only to the Tomcat server JVM. "
                "Mixing causes double-application of flags when scripts call java directly.",
                "export CATALINA_OPTS='-Xms{xms}g -Xmx{xmx}g ...'".format(
                    xms=xmx, xmx=xmx
                ),
            ),
        ]

        return [x for x in params if x is not None]

    # ── JVM flags renderer ───────────────────────────────────────────────────

    def _render_jvm_flags(self, xmx: float, meta: int, gc_t: int) -> str:
        inp  = self.inp

        gc_flags = {
            "G1GC":       f"-XX:+UseG1GC -XX:MaxGCPauseMillis=200 "
                          f"-XX:G1HeapRegionSize={'8m' if xmx >= 8 else '4m'} "
                          f"-XX:+UseStringDeduplication",
            "ZGC":        f"-XX:+UseZGC -XX:+ZGenerational"
                          if inp.java_version >= 21
                          else f"-XX:+UseZGC",
            "Shenandoah": f"-XX:+UseShenandoahGC -XX:ShenandoahGCMode=adaptive",
            "ParallelGC": f"-XX:+UseParallelGC",
        }.get(inp.gc_type, "-XX:+UseG1GC")

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX CATALINA_OPTS  [{inp.mode.value.upper():8s}]  "
            f"Java {inp.java_version}  RAM={inp.ram_gb}GB       ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"# Add to: /opt/tomcat/bin/setenv.sh

"
            f"export CATALINA_OPTS="\
"
            f"  # ── Heap ──────────────────────────────────────────────────
"
            f"  -Xms{xmx}g -Xmx{xmx}g \
"
            f"  -XX:MaxMetaspaceSize={meta}m \
"
            f"  -XX:MetaspaceSize={meta//2}m \
"
            f"  # ── GC ───────────────────────────────────────────────────
"
            f"  {gc_flags} \
"
            f"  -XX:ParallelGCThreads={gc_t} \
"
            f"  -XX:ConcGCThreads={max(1, gc_t//4)} \
"
            f"  # ── Safety ───────────────────────────────────────────────
"
            f"  -XX:+HeapDumpOnOutOfMemoryError \
"
            f"  -XX:HeapDumpPath=/var/log/tomcat/heapdump.hprof \
"
            f"  -XX:+ExitOnOutOfMemoryError \
"
            f"  # ── Observability ────────────────────────────────────────
"
            f"  -Xlog:gc*:file=/var/log/tomcat/gc.log:time,uptime:filecount=5,filesize=20m \
"
            f"  -Dcom.sun.management.jmxremote \
"
            f"  -Dcom.sun.management.jmxremote.port=9010 \
"
            f"  -Dcom.sun.management.jmxremote.authenticate=false \
"
            f"  -Dcom.sun.management.jmxremote.ssl=false \
"
            f"  # ── Startup performance ──────────────────────────────────
"
            f"  -XX:TieredStopAtLevel=4 \
"
            f"  -XX:+OptimizeStringConcat \
"
            f"  -Djava.awt.headless=true""
        )

    # ── server.xml renderer ──────────────────────────────────────────────────

    def _render_server_xml(self, max_t: int, xmx: float) -> str:
        inp  = self.inp
        mst  = self._min_spare_threads(max_t)
        ac   = self._accept_count(max_t)
        proto = f"org.apache.coyote.http11.Http11{'Nio2' if inp.connector_type == 'NIO2' else 'Nio' if inp.connector_type == 'NIO' else 'Apr'}Protocol"

        comp_attrs = (
            '
             compression="on"'
            '
             compressionMinSize="2048"'
            '
             compressibleMimeType="text/html,text/xml,text/plain,'
            'text/css,application/json,application/javascript"'
        ) if inp.compression_enabled else ""

        return (
            f"<!-- ╔════════════════════════════════════════════════════════╗ -->
"
            f"<!-- ║  VAREX server.xml  [{inp.mode.value.upper():8s}]  "
            f"Tomcat + Java {inp.java_version}          ║ -->
"
            f"<!-- ╚════════════════════════════════════════════════════════╝ -->

"
            f'<Connector port="8080"
'
            f'           protocol="{proto}"
'
            f'           maxThreads="{max_t}"
'
            f'           minSpareThreads="{mst}"
'
            f'           acceptCount="{ac}"
'
            f'           maxConnections="{max_t * 10}"
'
            f'           connectionTimeout="20000"
'
            f'           keepAliveTimeout="15000"
'
            f'           maxKeepAliveRequests="200"
'
            f'           server="Apache"
'
            f'           xpoweredBy="false"'
            f'{comp_attrs}
'
            f'           redirectPort="8443" />

'
            f'<!-- Disable AJP unless using mod_jk -->
'
            f'<!-- <Connector protocol="AJP/1.3" port="8009" ... /> -->

'
            f'<Engine name="Catalina" defaultHost="localhost" jvmRoute="node1">
'
            f'  <Host name="localhost" appBase="webapps"
'
            f'        unpackWARs="true" autoDeploy="false"
'
            f'        deployOnStartup="true">
'
            f'    <Valve className="org.apache.catalina.valves.AccessLogValve"
'
            f'           directory="logs" prefix="access_log" suffix=".txt"
'
            f'           pattern="%h %t &quot;%r&quot; %s %b %D" />
'
            f'    <Valve className="org.apache.catalina.valves.ErrorReportValve"
'
            f'           showReport="false" showServerInfo="false" />
'
            f'  </Host>
'
            f'</Engine>
'
        )

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, max_t: int, xmx: float, meta: int) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.max_threads and ex.max_threads < max_t * 0.5:
            findings.append(
                f"[MAJOR] maxThreads={ex.max_threads} is < 50% of Goetz-recommended {max_t}. "
                "Requests will queue and timeout under normal load."
            )
        if ex.max_threads and ex.max_threads > 1000:
            findings.append(
                f"[MAJOR] maxThreads={ex.max_threads} > 1000. "
                f"Each thread uses ~1MB stack → {ex.max_threads}MB RAM for stacks alone. "
                "This signals a thread-per-connection BIO connector, not NIO."
            )
        if ex.xmx_gb:
            if ex.xmx_gb > self.inp.ram_gb * 0.85:
                findings.append(
                    f"[MAJOR] -Xmx={ex.xmx_gb}GB = {ex.xmx_gb/self.inp.ram_gb*100:.0f}% of RAM. "
                    "Less than 15% RAM left for OS + Metaspace + off-heap. "
                    f"Recommended: -Xmx={xmx}GB (heap_ratio={self.inp.heap_ratio})."
                )
            if ex.xms_gb and ex.xms_gb != ex.xmx_gb:
                findings.append(
                    f"[MAJOR] -Xms={ex.xms_gb}GB ≠ -Xmx={ex.xmx_gb}GB. "
                    "Heap will expand under load, triggering Full GC during resize. "
                    "Set Xms=Xmx to pre-allocate heap and eliminate resize pauses."
                )
        if ex.gc_type == "ParallelGC" and self.inp.gc_type != "ParallelGC":
            findings.append(
                f"[MAJOR] GC=ParallelGC for a web workload. "
                "ParallelGC stop-the-world pauses can exceed 1–10s on large heaps. "
                f"Switch to {self.inp.gc_type} for latency-sensitive HTTP workloads."
            )
        if ex.metaspace_mb and ex.metaspace_mb < 256:
            findings.append(
                f"[MAJOR] MaxMetaspaceSize={ex.metaspace_mb}MB is very low. "
                "Spring Boot / Jakarta EE loads 5K–15K classes. "
                f"Risk of OutOfMemoryError: Metaspace. Recommended: {meta}MB."
            )
        if ex.connection_timeout and ex.connection_timeout > 30_000:
            findings.append(
                f"[MEDIUM] connectionTimeout={ex.connection_timeout}ms "
                f"({ex.connection_timeout//1000}s). "
                "Slow clients hold Tomcat threads for extended periods. Reduce to 20000ms."
            )
        if ex.connector_protocol == "HTTP/1.1":
            findings.append(
                "[MEDIUM] connector protocol=HTTP/1.1 uses old BIO (blocking I/O). "
                "One OS thread blocked per connection. Replace with Http11NioProtocol "
                "(NIO, event-driven) for 10x better concurrency."
            )
        if ex.compression == "off":
            findings.append(
                "[MEDIUM] compression=off. JSON/HTML responses sent uncompressed. "
                "Enable compression to reduce bandwidth by 60–80%."
            )
        if ex.min_spare_threads and ex.min_spare_threads < 10:
            findings.append(
                f"[MEDIUM] minSpareThreads={ex.min_spare_threads}. "
                "Too few idle threads — burst requests will wait for thread creation (5–20ms each)."
            )
        for k, v in ex.os_sysctl.items():
            try:
                if k == "transparent_hugepage" and v in ("always", "madvise"):
                    findings.append(
                        f"[MAJOR] transparent_hugepage={v}. "
                        "JVM GC fork-like operations experience latency spikes. "
                        "Set to never."
                    )
                if k == "net.core.somaxconn" and int(v) < 512:
                    findings.append(
                        f"[MEDIUM] net.core.somaxconn={v}. "
                        "Tomcat acceptCount is capped by this OS value. Silent connection drops."
                    )
            except ValueError:
                pass

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> TomcatOutput:
        max_t = self._goetz_threads()
        xmx   = self._xmx_gb()
        meta  = self._metaspace_mb()
        gc_t  = self._gc_threads()
        mst   = self._min_spare_threads(max_t)
        ac    = self._accept_count(max_t)

        all_params = self._build_params(max_t, xmx, meta, gc_t)

        os_engine = OSTuningEngine(
            cpu         = self.inp.cpu_cores,
            ram_gb      = self.inp.ram_gb,
            max_conns   = max(max_t * 10, self.inp.target_concurrency * 4),
            os_type     = self.inp.os_type,
            existing    = dict(self.inp.existing.os_sysctl),
            disable_thp = True,  # JVM GC sensitive to THP
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        return TomcatOutput(
            mode                  = self.inp.mode,
            max_threads           = max_t,
            min_spare_threads     = mst,
            accept_count          = ac,
            xms_gb                = xmx,
            xmx_gb                = xmx,
            metaspace_mb          = meta,
            gc_threads            = gc_t,
            goetz_formula_trace   = self._goetz_trace(max_t),
            server_xml_snippet    = self._render_server_xml(max_t, xmx),
            jvm_flags             = self._render_jvm_flags(xmx, meta, gc_t),
            major_params          = major,
            medium_params         = medium,
            minor_params          = minor,
            os_sysctl_conf        = os_engine.sysctl_block(),
            ha_suggestions=[
                "Run 2+ Tomcat nodes behind NGINX upstream with least_conn load balancing.",
                "Use Apache mod_cluster or NGINX with sticky sessions for stateful apps.",
                "Session replication: Tomcat DeltaManager (small clusters) or "
                "Redis-backed sessions (large clusters) via Tomcat Redis Session Manager.",
                "Set jvmRoute in Engine element + sticky session cookie for session affinity.",
                "Use Spring Boot Actuator /health endpoint for LB health checks.",
                "Container deployment: set -XX:+UseContainerSupport (Java 10+) so JVM "
                "reads CPU/memory from cgroup limits, not host totals.",
            ],
            performance_warnings=[w for w in [
                (f"target_concurrency ({self.inp.target_concurrency}) > maxThreads ({max_t}). "
                 "Requests will queue. Increase CPU cores or RAM.")
                if self.inp.target_concurrency > max_t else None,

                ("ParallelGC selected — stop-the-world pauses of 1–10s on large heaps. "
                 "Use G1GC or ZGC for HTTP workloads.")
                if self.inp.gc_type == "ParallelGC" else None,

                (f"Heap ({xmx}GB) > 32GB: G1GC may pause >500ms. "
                 "Consider ZGC (-XX:+UseZGC) for sub-millisecond pauses.")
                if xmx > 32 and self.inp.gc_type == "G1GC" else None,

                ("java_version < 11: many JVM optimisations and GC improvements unavailable. "
                 "Upgrade to Java 17 LTS.")
                if self.inp.java_version < 11 else None,

                ("SSL enabled at Tomcat. For production, terminate TLS at NGINX/LB to offload "
                 "crypto overhead from application threads.")
                if self.inp.ssl_enabled else None,
            ] if w],
            capacity_warning = self._capacity_warning(
                self.inp.target_concurrency, max_t, "Tomcat maxThreads"
            ),
            audit_findings = self._audit(max_t, xmx, meta)
                             if self.inp.mode == CalcMode.EXISTING else [],
        )
