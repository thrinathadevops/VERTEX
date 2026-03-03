"""
app/calculators/mongodb_calculator.py
======================================
MongoDB tuning calculator — NEW and EXISTING modes.

WiredTiger memory formula
-------------------------
wiredTigerCacheSizeGB = (RAM - 1GB) × 50%  (MongoDB default)
maxConnections        = min(cpu_cores × 200, 65536)
oplogSizeMB           = max(1024, disk_size_gb × 5%)
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.mongodb import MongoDBInput, MongoDBOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class MongoDBCalculator(BaseCalculator):

    def __init__(self, inp: MongoDBInput) -> None:
        self._require_positive(inp.cpu_cores,  "cpu_cores")
        self._require_positive(inp.ram_gb,     "ram_gb")
        self.inp = inp

    def _wt_cache_gb(self) -> float:
        return round(max(0.25, (self.inp.ram_gb - 1) * 0.50), 2)

    def _oplog_mb(self) -> int:
        return max(1024, int(self.inp.disk_size_gb * 0.05 * 1024))

    def _max_connections(self) -> int:
        return min(self.inp.cpu_cores * 200, 65536)

    def _journal_commit_interval(self) -> int:
        if self.inp.workload_type == "operational":
            return 50
        return 100

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        wt   = self._wt_cache_gb()
        opl  = self._oplog_mb()
        mc   = self._max_connections()
        jci  = self._journal_commit_interval()

        params = [
            p(
                "storage.wiredTiger.engineConfig.cacheSizeGB", str(wt), M,
                f"WiredTiger cache = (RAM - 1GB) × 50% = ({inp.ram_gb}-1) × 0.5 = {wt}GB. "
                "MongoDB default uses this formula automatically but explicitly setting it "
                "prevents surprises when RAM changes. "
                "Remaining RAM is used by: OS page cache (file I/O), connection overhead, "
                "aggregation pipelines, and index builds.",
                f"storage:\n  wiredTiger:\n    engineConfig:\n      cacheSizeGB: {wt}",
                str(ex.wired_tiger_cache_size_gb) if ex.wired_tiger_cache_size_gb else None,
                safe=False,
            ),
            p(
                "net.maxIncomingConnections", str(mc), M,
                f"Max concurrent connections = min(cpu_cores × 200, 65536) = {mc}. "
                "Each connection uses ~1MB RAM (thread stack). "
                "For high connection counts, use MongoDB connection pooling in drivers.",
                f"net:\n  maxIncomingConnections: {mc}",
                str(ex.max_connections) if ex.max_connections else None,
            ),
            p(
                "replication.oplogSizeMB", str(opl), M,
                f"Oplog size = max(1024MB, disk × 5%) = {opl}MB. "
                "The oplog is a capped collection of write operations for replication. "
                "Too small → secondaries fall behind → full resync required. "
                "Size to hold at least 24-72 hours of write activity.",
                f"replication:\n  oplogSizeMB: {opl}",
                str(ex.oplog_size_mb) if ex.oplog_size_mb else None,
                safe=False,
            ) if inp.replica_set else None,
            p(
                "security.authorization", "enabled", M,
                "Authentication and authorization MUST be enabled in production. "
                "Default: disabled — any client with network access has full admin rights. "
                "Similar to Redis without requirepass.",
                "security:\n  authorization: enabled",
                "enabled" if ex.auth_enabled else "disabled",
                safe=False,
            ),
            p(
                "storage.journal.enabled", "true", M,
                "Write-ahead journal for crash recovery. "
                "Without journal: data corruption on unclean shutdown. "
                "Default enabled since MongoDB 2.0. Never disable in production.",
                "storage:\n  journal:\n    enabled: true",
                "true" if ex.journal_enabled else "false",
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "storage.journal.commitIntervalMs", str(jci), MED,
                f"Journal flush interval = {jci}ms. "
                f"{'Operational/OLTP: 50ms for lower data loss window.' if jci == 50 else 'Analytics: 100ms (default) balances throughput vs durability.'} "
                "Data written between journal flushes is at risk on crash.",
                f"storage:\n  journal:\n    commitIntervalMs: {jci}",
                str(ex.journal_commit_interval) if ex.journal_commit_interval else None,
            ),
            p(
                "operationProfiling.slowOpThresholdMs", "100", MED,
                "Log operations taking >100ms. Default 100ms is reasonable. "
                "Use db.setProfilingLevel(1) for detailed query profiling.",
                "operationProfiling:\n  slowOpThresholdMs: 100\n  mode: slowOp",
            ),
            p(
                "net.ssl.mode", "requireSSL" if inp.replica_set else "preferSSL", MED,
                "Enable TLS for client and inter-node communication. "
                "requireSSL: reject non-TLS connections (recommended for replication).",
                f"net:\n  tls:\n    mode: {'requireTLS' if inp.replica_set else 'preferTLS'}",
                ex.ssl_mode,
            ),
            p(
                "storage.wiredTiger.collectionConfig.blockCompressor", "snappy", MED,
                "Snappy compression: ~70% compression ratio with minimal CPU overhead. "
                "zstd: better compression (~80%) but higher CPU. "
                "For analytics: zstd. For operational: snappy (default).",
                "storage:\n  wiredTiger:\n    collectionConfig:\n      blockCompressor: snappy",
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "setParameter.tcmallocReleaseRate", "5.0", MIN,
                "How aggressively tcmalloc returns unused memory to OS. "
                "Higher values = more frequent release = lower RSS. "
                "Default 1.0. Set to 5.0 for containers with memory limits.",
                "setParameter:\n  tcmallocReleaseRate: 5.0",
            ),
            p(
                "systemLog.logRotate", "reopen", MIN,
                "Use 'reopen' for logrotate compatibility. "
                "Send SIGUSR1 to mongod to trigger log rotation.",
                "systemLog:\n  logRotate: reopen\n  verbosity: 0",
            ),
        ]

        return [x for x in params if x is not None]

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if not ex.auth_enabled:
            findings.append(
                "[MAJOR] Authorization disabled. Any client has full admin access. "
                "Enable security.authorization immediately."
            )
        if ex.wired_tiger_cache_size_gb and ex.wired_tiger_cache_size_gb > self.inp.ram_gb * 0.7:
            findings.append(
                f"[MAJOR] WiredTiger cache ({ex.wired_tiger_cache_size_gb}GB) exceeds 70% of RAM. "
                f"Risk of OOM. Recommended: {self._wt_cache_gb()}GB."
            )
        if ex.ssl_mode in (None, "disabled") and self.inp.replica_set:
            findings.append(
                "[MEDIUM] TLS disabled with replica set. Inter-node traffic is plaintext."
            )

        for k, v in ex.os_sysctl.items():
            if k == "transparent_hugepage" and v in ("always", "madvise"):
                findings.append(
                    f"[MAJOR] transparent_hugepage={v}. MongoDB requires THP disabled. "
                    "Causes allocation stalls and unpredictable latency."
                )
            if k == "vm.swappiness":
                try:
                    if int(v) > 10:
                        findings.append(
                            f"[MEDIUM] vm.swappiness={v}. Database pages being swapped = "
                            "catastrophic latency. Set to 1."
                        )
                except ValueError:
                    pass

        return findings

    def _render_conf(self) -> str:
        inp = self.inp
        wt  = self._wt_cache_gb()
        mc  = self._max_connections()
        opl = self._oplog_mb()
        jci = self._journal_commit_interval()

        repl_block = ""
        if inp.replica_set:
            repl_block = (
                "\nreplication:\n"
                f"  oplogSizeMB: {opl}\n"
                "  replSetName: rs0\n"
            )

        sharding_block = ""
        if inp.sharded:
            sharding_block = (
                "\nsharding:\n"
                "  clusterRole: shardsvr\n"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗\n"
            f"# ║  VAREX mongod.conf  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}      ║\n"
            f"# ╚══════════════════════════════════════════════════════════════╝\n\n"
            f"storage:\n"
            f"  dbPath: /data/db\n"
            f"  journal:\n"
            f"    enabled: true\n"
            f"    commitIntervalMs: {jci}\n"
            f"  wiredTiger:\n"
            f"    engineConfig:\n"
            f"      cacheSizeGB: {wt}\n"
            f"      journalCompressor: snappy\n"
            f"    collectionConfig:\n"
            f"      blockCompressor: snappy\n"
            f"    indexConfig:\n"
            f"      prefixCompression: true\n\n"
            f"net:\n"
            f"  port: 27017\n"
            f"  maxIncomingConnections: {mc}\n"
            f"  tls:\n"
            f"    mode: {'requireTLS' if inp.replica_set else 'preferTLS'}\n\n"
            f"security:\n"
            f"  authorization: enabled\n\n"
            f"operationProfiling:\n"
            f"  slowOpThresholdMs: 100\n"
            f"  mode: slowOp\n\n"
            f"systemLog:\n"
            f"  destination: file\n"
            f"  path: /var/log/mongodb/mongod.log\n"
            f"  logAppend: true\n"
            f"  logRotate: reopen\n"
            f"{repl_block}{sharding_block}\n"
            f"setParameter:\n"
            f"  tcmallocReleaseRate: 5.0\n"
        )

    def generate(self) -> MongoDBOutput:
        wt  = self._wt_cache_gb()
        opl = self._oplog_mb()
        mc  = self._max_connections()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = mc,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
            disable_thp = True,
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            "Deploy a 3-member replica set minimum (Primary + Secondary + Arbiter or 3 data nodes).",
            "Use readPreference=secondaryPreferred for read scaling.",
            "For write-heavy workloads: consider sharding by a high-cardinality shard key.",
            "Enable Change Streams for event-driven architectures.",
        ]

        perf_warnings = [w for w in [
            (f"storage_type=hdd. MongoDB WiredTiger random reads are severely limited on HDD.")
            if self.inp.storage_type == "hdd" else None,
        ] if w]

        return MongoDBOutput(
            mode                        = self.inp.mode,
            wired_tiger_cache_gb        = wt,
            recommended_oplog_mb        = opl,
            recommended_max_connections = mc,
            mongod_conf_snippet         = self._render_conf(),
            major_params                = major,
            medium_params               = medium,
            minor_params                = minor,
            os_sysctl_conf              = os_engine.sysctl_block(),
            ha_suggestions              = ha_suggestions,
            performance_warnings        = perf_warnings,
            capacity_warning            = self._capacity_warning(
                wt, self.inp.ram_gb * 0.7, "WiredTiger cache vs 70% RAM"
            ),
            audit_findings              = self._audit()
                                          if self.inp.mode == CalcMode.EXISTING else [],
        )
