from __future__ import annotations
import math
from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.core.models import TuningParam
from app.schemas.tomcat import TomcatInput, TomcatOutput

M, MED, MIN = ImpactLevel.MAJOR, ImpactLevel.MEDIUM, ImpactLevel.MINOR


class TomcatCalculator(BaseCalculator):

    def __init__(self, inp: TomcatInput) -> None:
        self._require_positive(inp.cpu_cores,                 "cpu_cores")
        self._require_positive(inp.expected_concurrent_users, "expected_concurrent_users")
        self._require_positive(inp.avg_request_time_ms,       "avg_request_time_ms")
        self._require_positive(inp.avg_cpu_time_ms,           "avg_cpu_time_ms")
        if inp.avg_cpu_time_ms > inp.avg_request_time_ms:
            raise ValueError("avg_cpu_time_ms cannot exceed avg_request_time_ms")
        self.inp = inp

    def _wait_ms(self) -> int:
        return self.inp.avg_request_time_ms - self.inp.avg_cpu_time_ms

    def _max_threads(self) -> int:
        # Goetz formula: N_threads = N_cpu * U_cpu * (1 + W/C)
        ratio = 1 + self._wait_ms() / self.inp.avg_cpu_time_ms
        raw   = math.ceil(self.inp.cpu_cores * self.inp.target_cpu_utilization * ratio)
        return max(self.inp.expected_concurrent_users, min(raw, 1000))

    def _min_spare(self) -> int:
        return max(10, self._max_threads() // 10)

    def _accept_count(self) -> int:
        return max(50, int(self.inp.expected_concurrent_users * 0.2))

    def _heap_gb(self) -> tuple[float, float]:
        xmx = self.inp.ram_gb * self.inp.jvm_heap_ratio
        xms = xmx * 0.5
        return round(xms, 2), round(xmx, 2)

    def _to_str(self, gb: float) -> str:
        mb = int(gb * 1024)
        return f"{mb}m" if mb < 1024 else f"{int(round(gb))}g"

    def _tomcat_params(self, mt, mst, ac, xms_s, xmx_s) -> list[TuningParam]:
        ex = self.inp.existing
        return [
            # MAJOR
            self._param("maxThreads",         str(mt),  M,
                "Goetz formula: cores × utilisation × (1 + wait/cpu). "
                "Too low → queue build-up; too high → GC pressure.",
                f'maxThreads="{mt}"',
                str(ex.max_threads) if ex.max_threads else None),
            self._param("Xmx (JVM heap max)",  xmx_s,  M,
                "Heap max drives GC frequency and OOM risk. "
                "Set to 70% RAM to leave room for off-heap and OS.",
                f"export CATALINA_OPTS=\"-Xmx{xmx_s}\"",
                ex.jvm_xmx),
            self._param("Xms (JVM heap init)", xms_s,  M,
                "Set to 50% Xmx to allow GC tuning room at startup.",
                f"export CATALINA_OPTS=\"-Xms{xms_s}\"",
                ex.jvm_xms),
            self._param("GC: G1GC",      "-XX:+UseG1GC", M,
                "G1GC delivers predictable low-pause GC vs CMS or Serial. "
                "Critical for latency-sensitive workloads.",
                "-XX:+UseG1GC -XX:MaxGCPauseMillis=200",
                ex.gc_type),
            # MEDIUM
            self._param("minSpareThreads",    str(mst), MED,
                "Pre-warmed threads = maxThreads/10. Prevents cold-start latency spikes.",
                f'minSpareThreads="{mst}"',
                str(ex.min_spare_threads) if ex.min_spare_threads else None),
            self._param("acceptCount",        str(ac),  MED,
                "TCP accept queue depth = 20% concurrent users. "
                "Overflow causes connection refused errors.",
                f'acceptCount="{ac}"',
                str(ex.accept_count) if ex.accept_count else None),
            self._param("connectionTimeout",  "20000",  MED,
                "20s connection timeout prevents thread pool exhaustion from slow clients.",
                'connectionTimeout="20000"',
                str(ex.connection_timeout_ms) if ex.connection_timeout_ms else None),
            self._param("protocol (NIO/NIO2/APR)", f"Http11{self.inp.connector_type}Protocol", MED,
                "NIO is non-blocking and scales better than BIO. "
                "APR gives native OS performance via JNI.",
                f'protocol="org.apache.coyote.http11.Http11{self.inp.connector_type}Protocol"',
                ex.connector_protocol),
            self._param("-XX:+ParallelRefProcEnabled", "on", MED,
                "Parallel reference processing reduces GC pause time under high object churn.",
                "-XX:+ParallelRefProcEnabled"),
            # MINOR
            self._param("keepAliveTimeout",  "20000", MIN,
                "How long to keep idle HTTP keep-alive connections open (ms).",
                'keepAliveTimeout="20000"'),
            self._param("maxKeepAliveRequests", "100", MIN,
                "Limits keep-alive requests per connection to prevent monopolisation.",
                'maxKeepAliveRequests="100"'),
            self._param("enableLookups",      "false", MIN,
                "DNS reverse-lookup per request adds latency. Always disable in production.",
                'enableLookups="false"'),
            self._param("compression",        "on",    MIN,
                "Enable gzip compression for text responses > 2 KB.",
                'compression="on" compressionMinSize="2048"'),
            self._param("-Djava.awt.headless", "true", MIN,
                "Prevents AWT initialisation errors on headless servers.",
                "-Djava.awt.headless=true"),
        ]

    def _audit(self, mt: int) -> list[str]:
        findings: list[str] = []
        ex = self.inp.existing
        if ex.max_threads and ex.max_threads < mt * 0.5:
            findings.append(
                f"maxThreads={ex.max_threads} is less than half the recommended {mt}. "
                "Requests will queue under load."
            )
        if ex.gc_type and "serial" in ex.gc_type.lower():
            findings.append(
                "SerialGC detected – single-threaded GC will cause stop-the-world pauses "
                "of 1-5s on large heaps. Migrate to G1GC or ZGC."
            )
        if ex.jvm_xmx:
            xmx_str = ex.jvm_xmx.lower().replace("g", "").replace("m", "")
            try:
                xmx_val = float(xmx_str) * (1024 if "g" in ex.jvm_xmx.lower() else 1) / 1024
                _, rec_xmx = self._heap_gb()
                if xmx_val < rec_xmx * 0.5:
                    findings.append(
                        f"JVM Xmx ({ex.jvm_xmx}) is less than half the recommended "
                        f"{self._to_str(rec_xmx)}. Frequent GC cycles expected."
                    )
            except ValueError:
                pass
        if ex.accept_count and ex.accept_count < 50:
            findings.append(
                f"acceptCount={ex.accept_count} is very low. "
                "Connection-refused errors under burst traffic."
            )
        for k, v in (ex.os_sysctl or {}).items():
            if k == "net.core.somaxconn" and int(v) < 1024:
                findings.append(f"OS somaxconn={v}. Tomcat accept queue silently truncated at OS level.")
        return findings

    def _server_xml(self, mt, mst, ac) -> str:
        return f"""<!-- ── VAREX server.xml Connector ({self.inp.mode.value.upper()} mode) ── -->
<Connector port="8080"
           protocol="org.apache.coyote.http11.Http11{self.inp.connector_type}Protocol"
           maxThreads="{mt}"
           minSpareThreads="{mst}"
           acceptCount="{ac}"
           connectionTimeout="20000"
           keepAliveTimeout="20000"
           maxKeepAliveRequests="100"
           compression="on"
           compressionMinSize="2048"
           disableUploadTimeout="true"
           enableLookups="false"
           URIEncoding="UTF-8" />
"""

    def _jvm_args(self, xms_s, xmx_s) -> str:
        return (f"-Xms{xms_s} -Xmx{xmx_s} "
                "-XX:+UseG1GC -XX:MaxGCPauseMillis=200 "
                "-XX:+ParallelRefProcEnabled -XX:+DisableExplicitGC "
                "-Djava.awt.headless=true -Dfile.encoding=UTF-8")

    def _ha_suggestions(self) -> list[str]:
        return [
            "Run ≥2 Tomcat instances behind NGINX or AWS ALB.",
            "Externalise HTTP sessions to Redis (Spring Session / Redisson) for stateless HA.",
            "Enable Tomcat Cluster DeltaManager for in-memory session replication.",
            "Configure JMX remote monitoring for GC and thread-pool visibility.",
            "Use Kubernetes HPA on CPU/request-latency metrics to auto-scale Tomcat pods.",
        ]

    def _perf_warnings(self, mt: int) -> list[str]:
        w = []
        if self.inp.expected_concurrent_users > mt:
            w.append(f"concurrent_users ({self.inp.expected_concurrent_users}) > maxThreads ({mt}).")
        _, xmx = self._heap_gb()
        if xmx < 1:
            w.append("JVM heap < 1 GB – insufficient for any non-trivial workload.")
        if self.inp.avg_request_time_ms > 5000:
            w.append("Avg request time > 5s – consider async servlets or reactive stack.")
        if self.inp.cpu_cores < 2:
            w.append("Single CPU – severe thread contention expected.")
        return w

    def generate(self) -> TomcatOutput:
        mt  = self._max_threads()
        mst = self._min_spare()
        ac  = self._accept_count()
        xms, xmx = self._heap_gb()
        xms_s, xmx_s = self._to_str(xms), self._to_str(xmx)

        all_params = self._tomcat_params(mt, mst, ac, xms_s, xmx_s)

        os_engine = OSTuningEngine(
            cpu_cores=self.inp.cpu_cores,
            ram_gb=self.inp.ram_gb,
            max_conns=max(self.inp.expected_concurrent_users * 4, 10_000),
            os_type=self.inp.os_type,
            existing_params=dict(self.inp.existing.os_sysctl) if self.inp.existing else {},
            disable_thp=False,
        )
        all_params += os_engine.generate()

        return TomcatOutput(
            mode=self.inp.mode,
            max_threads=mt, min_spare_threads=mst, accept_count=ac,
            connection_timeout_ms=20_000,
            jvm_xms=xms_s, jvm_xmx=xmx_s,
            server_xml_snippet=self._server_xml(mt, mst, ac),
            jvm_args=self._jvm_args(xms_s, xmx_s),
            major_params=[p for p in all_params if p.impact == ImpactLevel.MAJOR],
            medium_params=[p for p in all_params if p.impact == ImpactLevel.MEDIUM],
            minor_params=[p for p in all_params if p.impact == ImpactLevel.MINOR],
            os_sysctl_conf=os_engine.sysctl_conf_block(),
            ha_suggestions=self._ha_suggestions(),
            performance_warnings=self._perf_warnings(mt),
            capacity_warning=self._capacity_warning(
                self.inp.expected_concurrent_users, mt, "Tomcat thread pool"),
            audit_findings=self._audit(mt) if self.inp.mode == CalcMode.EXISTING else [],
        )
