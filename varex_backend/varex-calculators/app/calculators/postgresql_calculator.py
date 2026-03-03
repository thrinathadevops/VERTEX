"""
app/calculators/postgresql_calculator.py
========================================
PostgreSQL tuning calculator — NEW and EXISTING modes.

Memory allocation strategy (PostgreSQL docs + pgtune)
-----------------------------------------------------
shared_buffers       = 25% of RAM  (PostgreSQL default: 128MB — far too low)
effective_cache_size = 75% of RAM  (tells planner how much OS page cache to expect)
work_mem             = (RAM × 25%) / max_connections
                       Each sort/hash/merge JOIN allocates up to work_mem.
                       Total peak usage ≈ work_mem × max_connections × 2-3 ops/query.
maintenance_work_mem = min(RAM / 16, 2GB)  — VACUUM, CREATE INDEX, ALTER TABLE ADD FK
wal_buffers          = min(shared_buffers / 32, 64MB) — WAL write buffer

Storage tuning
--------------
SSD/NVMe:  random_page_cost=1.1,  effective_io_concurrency=200
HDD:       random_page_cost=4.0,  effective_io_concurrency=2

Parallel query (PG 9.6+)
-------------------------
max_parallel_workers_per_gather = min(cpu_cores / 2, 4)  — OLTP
                                 = min(cpu_cores / 2, 8)  — OLAP

Checkpoint tuning
-----------------
checkpoint_completion_target = 0.9  (spread I/O across 90% of interval)
max_wal_size                 = 2GB  (OLTP) or 4GB (OLAP/DW)
min_wal_size                 = 1GB
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.postgresql import PostgreSQLInput, PostgreSQLOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class PostgreSQLCalculator(BaseCalculator):

    def __init__(self, inp: PostgreSQLInput) -> None:
        self._require_positive(inp.cpu_cores,       "cpu_cores")
        self._require_positive(inp.ram_gb,           "ram_gb")
        self._require_positive(inp.max_connections,  "max_connections")
        self.inp = inp

    # ── internal calculations ─────────────────────────────────────────────────

    def _shared_buffers_mb(self) -> int:
        """25% of RAM — the PostgreSQL recommendation."""
        return int(self.inp.ram_gb * 1024 * 0.25)

    def _effective_cache_size_mb(self) -> int:
        """75% of RAM — assumption about OS page cache availability."""
        return int(self.inp.ram_gb * 1024 * 0.75)

    def _work_mem_mb(self) -> int:
        """
        (RAM × 25%) / max_connections.
        Floor at 4MB (below this, sorts spill to disk on trivial queries).
        Cap at 1GB (single query shouldn't monopolise RAM).
        """
        wm = int(self.inp.ram_gb * 1024 * 0.25 / self.inp.max_connections)
        return max(4, min(wm, 1024))

    def _maintenance_work_mem_mb(self) -> int:
        """min(RAM/16, 2GB) — for VACUUM, CREATE INDEX."""
        return int(min(self.inp.ram_gb * 1024 / 16, 2048))

    def _wal_buffers_mb(self) -> int:
        """min(shared_buffers/32, 64MB). Floor at 4MB."""
        return max(4, min(self._shared_buffers_mb() // 32, 64))

    def _max_wal_size_gb(self) -> int:
        """2GB for OLTP, 4GB for OLAP/DW."""
        if self.inp.workload_type in ("olap", "data_warehouse"):
            return 4
        return 2

    def _random_page_cost(self) -> float:
        if self.inp.storage_type == "hdd":
            return 4.0
        return 1.1  # SSD/NVMe

    def _effective_io_concurrency(self) -> int:
        if self.inp.storage_type == "hdd":
            return 2
        if self.inp.storage_type == "nvme":
            return 256
        return 200  # SSD

    def _max_parallel_workers(self) -> int:
        return self.inp.cpu_cores

    def _max_parallel_workers_per_gather(self) -> int:
        if self.inp.workload_type in ("olap", "data_warehouse"):
            return min(self.inp.cpu_cores // 2, 8)
        return min(self.inp.cpu_cores // 2, 4)

    def _max_worker_processes(self) -> int:
        return max(self.inp.cpu_cores, 8)

    def _default_statistics_target(self) -> int:
        if self.inp.workload_type in ("olap", "data_warehouse"):
            return 500
        return 100

    def _huge_pages(self) -> str:
        """Enable huge pages for >=8GB shared_buffers (reduces TLB misses)."""
        if self._shared_buffers_mb() >= 8192:
            return "try"
        return "off"

    @staticmethod
    def _fmt_mem(mb: int) -> str:
        """Format MB to human-readable: '8GB', '512MB'."""
        if mb >= 1024 and mb % 1024 == 0:
            return f"{mb // 1024}GB"
        return f"{mb}MB"

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        sb   = self._shared_buffers_mb()
        ecs  = self._effective_cache_size_mb()
        wm   = self._work_mem_mb()
        mwm  = self._maintenance_work_mem_mb()
        wb   = self._wal_buffers_mb()
        mws  = self._max_wal_size_gb()
        rpc  = self._random_page_cost()
        eio  = self._effective_io_concurrency()
        mpw  = self._max_parallel_workers()
        mpwg = self._max_parallel_workers_per_gather()
        mwp  = self._max_worker_processes()
        dst  = self._default_statistics_target()

        params = [
            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "shared_buffers", self._fmt_mem(sb), M,
                f"PostgreSQL's main buffer cache = 25% of RAM = {self._fmt_mem(sb)}. "
                f"Default 128MB is absurdly low — wastes available RAM. "
                "PostgreSQL uses a double-buffering architecture: shared_buffers (PG-managed) "
                "+ OS page cache. Setting >40% of RAM causes diminishing returns because "
                "the OS page cache shrinks below useful levels.",
                f"shared_buffers = {self._fmt_mem(sb)}",
                ex.shared_buffers,
                safe=False,
            ),
            p(
                "effective_cache_size", self._fmt_mem(ecs), M,
                f"Planner hint = 75% of RAM = {self._fmt_mem(ecs)}. "
                "Does NOT allocate memory — tells the query planner how much data "
                "is likely already in OS page cache. Too low → planner avoids index scans "
                "in favor of sequential scans. Too high → planner overestimates cache hits.",
                f"effective_cache_size = {self._fmt_mem(ecs)}",
                ex.effective_cache_size,
            ),
            p(
                "work_mem", self._fmt_mem(wm), M,
                f"Per-operation sort/hash memory = {self._fmt_mem(wm)}. "
                f"Formula: (RAM × 25%) / max_connections = "
                f"({inp.ram_gb}GB × 256MB) / {inp.max_connections}. "
                "Each query can use multiple work_mem allocations (one per sort/hash node). "
                "Too low → sorts spill to disk temp files (100x slower). "
                "Too high × many connections → OOM risk.",
                f"work_mem = {self._fmt_mem(wm)}",
                ex.work_mem,
            ),
            p(
                "maintenance_work_mem", self._fmt_mem(mwm), M,
                f"VACUUM / CREATE INDEX / ALTER TABLE memory = {self._fmt_mem(mwm)}. "
                f"Formula: min(RAM/16, 2GB) = min({inp.ram_gb}GB/16, 2GB). "
                "Higher values make VACUUM and index creation significantly faster. "
                "Only one maintenance operation uses this at a time (per autovacuum worker). "
                "Capped at 2GB because PostgreSQL uses 32-bit integer for internal tracking.",
                f"maintenance_work_mem = {self._fmt_mem(mwm)}",
                ex.maintenance_work_mem,
            ),
            p(
                "max_connections", str(inp.max_connections), M,
                f"Maximum concurrent connections = {inp.max_connections}. "
                "Each connection consumes ~10MB of RAM (stack + work_mem). "
                f"At {inp.max_connections} connections: ~{inp.max_connections * 10 // 1024}GB RAM. "
                "Use PgBouncer for connection pooling if you need >200 concurrent connections. "
                "PostgreSQL performance degrades sharply above ~300 active connections.",
                f"max_connections = {inp.max_connections}",
                str(ex.max_connections) if ex.max_connections else None,
                safe=False,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "wal_buffers", self._fmt_mem(wb), MED,
                f"WAL write buffer = min(shared_buffers/32, 64MB) = {self._fmt_mem(wb)}. "
                "Buffers WAL data before flushing to disk. Default is auto-tuned from "
                "shared_buffers but only up to ~16MB. Higher values reduce WAL flush frequency "
                "under heavy write load.",
                f"wal_buffers = {self._fmt_mem(wb)}",
                ex.wal_buffers,
            ),
            p(
                "max_wal_size", f"{mws}GB", MED,
                f"Maximum WAL disk usage before checkpoint = {mws}GB. "
                f"{'OLAP/DW workloads benefit from larger WAL to reduce checkpoint frequency.' if mws == 4 else 'OLTP: 2GB balances recovery time vs I/O smoothing.'}. "
                "When WAL reaches max_wal_size, PostgreSQL triggers a checkpoint. "
                "Larger = fewer checkpoints = smoother I/O, but longer crash recovery.",
                f"max_wal_size = {mws}GB",
                ex.max_wal_size,
            ),
            p(
                "checkpoint_completion_target", "0.9", MED,
                "Spread checkpoint I/O across 90% of the checkpoint interval. "
                "Default 0.5 creates I/O spikes halfway through each checkpoint. "
                "0.9 smooths checkpoint writes over the full interval, reducing latency spikes. "
                "Production standard for all workloads.",
                "checkpoint_completion_target = 0.9",
                str(ex.checkpoint_completion_target) if ex.checkpoint_completion_target else None,
            ),
            p(
                "random_page_cost", str(rpc), MED,
                f"Cost of a non-sequential page read = {rpc}. "
                f"{'SSD/NVMe: 1.1 (random ≈ sequential).' if rpc < 2 else 'HDD: 4.0 (random is 40× slower than sequential).'} "
                "Default 4.0 was designed for spinning disks. On SSDs, this makes the planner "
                "avoid index scans in favor of sequential scans — exactly wrong.",
                f"random_page_cost = {rpc}",
                str(ex.random_page_cost) if ex.random_page_cost else None,
            ),
            p(
                "effective_io_concurrency", str(eio), MED,
                f"Concurrent I/O operations the disk can handle = {eio}. "
                "Used for bitmap heap scans and prefetch. "
                f"{'HDD: 2 (single spindle).' if eio <= 2 else f'SSD/NVMe: {eio} (parallel I/O channels).'} "
                "Default 1 dramatically under-utilises SSD/NVMe bandwidth.",
                f"effective_io_concurrency = {eio}",
                str(ex.effective_io_concurrency) if ex.effective_io_concurrency else None,
            ),
            p(
                "max_worker_processes", str(mwp), MED,
                f"Background worker process limit = {mwp}. "
                "Includes autovacuum workers, parallel query workers, logical replication. "
                "Set to at least cpu_cores. Too low → parallel queries are throttled.",
                f"max_worker_processes = {mwp}",
                str(ex.max_worker_processes) if ex.max_worker_processes else None,
                safe=False,
            ),
            p(
                "max_parallel_workers", str(mpw), MED,
                f"Global parallel query worker limit = {mpw}. "
                "Caps total concurrent parallel workers across all queries. "
                "Set equal to cpu_cores.",
                f"max_parallel_workers = {mpw}",
                str(ex.max_parallel_workers) if ex.max_parallel_workers else None,
                safe=False,
            ),
            p(
                "max_parallel_workers_per_gather", str(mpwg), MED,
                f"Per-query parallel workers = {mpwg}. "
                f"{'OLAP/DW: up to half of cores for heavy analytics.' if mpwg > 4 else 'OLTP: conservative — too many parallel workers starve other queries.'}",
                f"max_parallel_workers_per_gather = {mpwg}",
                str(ex.max_parallel_workers_per_gather) if ex.max_parallel_workers_per_gather else None,
                safe=False,
            ),
            p(
                "default_statistics_target", str(dst), MED,
                f"Statistics sampling depth = {dst}. "
                f"{'OLAP/DW: 500 — better cardinality estimates for complex joins.' if dst > 100 else 'OLTP: 100 (default) — sufficient for simple queries.'} "
                "Higher values make ANALYZE slower but produce better query plans.",
                f"default_statistics_target = {dst}",
                str(ex.default_statistics_target) if ex.default_statistics_target else None,
            ),
            p(
                "huge_pages", self._huge_pages(), MED,
                f"Huge pages setting = '{self._huge_pages()}'. "
                f"{'Shared buffers ≥8GB: huge pages reduce TLB misses by 30-50%, improving cache performance.' if self._huge_pages() == 'try' else 'Shared buffers <8GB: huge pages overhead exceeds benefit.'} "
                "'try' = use if available, fall back gracefully. 'on' = fail if unavailable.",
                f"huge_pages = {self._huge_pages()}",
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "log_min_duration_statement", "1000", MIN,
                "Log queries taking >1000ms (1 second). "
                "Essential for identifying slow queries without pg_stat_statements overhead. "
                "Use pg_stat_statements for comprehensive stats, this for immediate alerts.",
                "log_min_duration_statement = 1000  # ms",
                str(ex.log_min_duration_statement) if ex.log_min_duration_statement else None,
            ),
            p(
                "log_checkpoints", "on", MIN,
                "Log checkpoint activity including timing and buffer stats. "
                "Without this, you cannot identify checkpoint-induced latency spikes.",
                "log_checkpoints = on",
            ),
            p(
                "log_connections + log_disconnections", "on", MIN,
                "Log connection lifecycle. Essential for diagnosing connection storms, "
                "connection pool leaks, and authentication failures.",
                "log_connections = on\nlog_disconnections = on",
            ),
            p(
                "log_lock_waits", "on", MIN,
                "Log when a query waits >1s for a lock. "
                "Identifies lock contention before it becomes a production incident.",
                "log_lock_waits = on\ndeadlock_timeout = 1s",
            ),
            p(
                "shared_preload_libraries", "'pg_stat_statements'", MIN,
                "pg_stat_statements: essential for query performance monitoring. "
                "Tracks execution counts, total time, rows, and I/O for every query. "
                "Overhead: <2% CPU. Without it: zero visibility into query performance.",
                "shared_preload_libraries = 'pg_stat_statements'\npg_stat_statements.track = all",
                safe=False,
            ),
            p(
                "autovacuum tuning", "conservative defaults", MIN,
                "autovacuum_max_workers = 3 (default). "
                "autovacuum_vacuum_scale_factor = 0.1 (vacuum when 10% of rows are dead). "
                "autovacuum_analyze_scale_factor = 0.05 (analyze when 5% of rows change). "
                "For tables >10M rows: set per-table autovacuum_vacuum_threshold.",
                "autovacuum = on\n"
                "autovacuum_max_workers = 3\n"
                "autovacuum_vacuum_scale_factor = 0.1\n"
                "autovacuum_analyze_scale_factor = 0.05\n"
                "autovacuum_vacuum_cost_delay = 2ms",
            ),
            p(
                "ssl", "on" if inp.replication else "recommended", MIN,
                "Enable SSL/TLS for client connections. Mandatory for replication across "
                "networks. Use scram-sha-256 for password hashing (not md5).",
                "ssl = on\npassword_encryption = scram-sha-256",
                "on" if ex.ssl_enabled else "off",
            ),
        ]

        return [x for x in params if x is not None]

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing
        sb = self._shared_buffers_mb()

        if ex.shared_buffers and self._parse_mem(ex.shared_buffers) < sb * 0.5:
            findings.append(
                f"[MAJOR] shared_buffers={ex.shared_buffers} is less than half the "
                f"recommended {self._fmt_mem(sb)}. Massive performance loss from excessive disk I/O."
            )
        if ex.max_connections and ex.max_connections > 500:
            findings.append(
                f"[MAJOR] max_connections={ex.max_connections} without connection pooling. "
                "PostgreSQL performance degrades sharply above 300. Use PgBouncer."
            )
        if ex.random_page_cost and ex.random_page_cost >= 4.0 and self.inp.storage_type != "hdd":
            findings.append(
                f"[MAJOR] random_page_cost={ex.random_page_cost} on {self.inp.storage_type}. "
                f"Set to {self._random_page_cost()} — planner is avoiding index scans unnecessarily."
            )
        if ex.effective_io_concurrency is not None and ex.effective_io_concurrency <= 2 and self.inp.storage_type != "hdd":
            findings.append(
                f"[MEDIUM] effective_io_concurrency={ex.effective_io_concurrency} on {self.inp.storage_type}. "
                f"Set to {self._effective_io_concurrency()} to utilize parallel I/O channels."
            )
        if ex.work_mem and self._parse_mem(ex.work_mem) < 4:
            findings.append(
                f"[MEDIUM] work_mem={ex.work_mem} is very low. "
                "Most sorts/hashes will spill to disk temp files."
            )
        if ex.checkpoint_completion_target and ex.checkpoint_completion_target < 0.7:
            findings.append(
                f"[MEDIUM] checkpoint_completion_target={ex.checkpoint_completion_target}. "
                "I/O spikes during checkpoints. Set to 0.9."
            )
        if not ex.ssl_enabled and self.inp.replication:
            findings.append(
                "[MEDIUM] SSL disabled with replication enabled. "
                "Replication data transmitted in plaintext across the network."
            )

        # OS-level audit
        for k, v in ex.os_sysctl.items():
            try:
                if k == "vm.overcommit_memory" and v != "2":
                    findings.append(
                        f"[MEDIUM] vm.overcommit_memory={v}. "
                        "PostgreSQL recommends vm.overcommit_memory=2 with "
                        "vm.overcommit_ratio=80 to prevent OOM killer."
                    )
                if k == "vm.swappiness" and int(v) > 10:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. "
                        "Shared buffers being swapped to disk = catastrophic latency. "
                        "Set to 1 for database servers."
                    )
            except ValueError:
                pass

        return findings

    @staticmethod
    def _parse_mem(val: str) -> int:
        """Parse memory string like '128MB', '8GB' to MB."""
        val = val.strip().upper()
        try:
            if val.endswith("GB"):
                return int(float(val[:-2]) * 1024)
            if val.endswith("MB"):
                return int(float(val[:-2]))
            if val.endswith("KB"):
                return max(1, int(float(val[:-2]) / 1024))
            return int(val)  # assume bytes → MB
        except (ValueError, TypeError):
            return 0

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self) -> str:
        inp  = self.inp
        sb   = self._fmt_mem(self._shared_buffers_mb())
        ecs  = self._fmt_mem(self._effective_cache_size_mb())
        wm   = self._fmt_mem(self._work_mem_mb())
        mwm  = self._fmt_mem(self._maintenance_work_mem_mb())
        wb   = self._fmt_mem(self._wal_buffers_mb())
        mws  = self._max_wal_size_gb()
        rpc  = self._random_page_cost()
        eio  = self._effective_io_concurrency()
        mpw  = self._max_parallel_workers()
        mpwg = self._max_parallel_workers_per_gather()
        mwp  = self._max_worker_processes()
        dst  = self._default_statistics_target()

        repl_block = ""
        if inp.replication:
            repl_block = (
                "\n# ── Replication ─────────────────────────────────────────────\n"
                "wal_level = replica\n"
                "max_wal_senders = 10\n"
                "max_replication_slots = 10\n"
                "hot_standby = on\n"
                "hot_standby_feedback = on\n"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗\n"
            f"# ║  VAREX postgresql.conf  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}       ║\n"
            f"# ╚══════════════════════════════════════════════════════════════╝\n\n"
            f"# ── Memory ───────────────────────────────────────────────────\n"
            f"shared_buffers = {sb}\n"
            f"effective_cache_size = {ecs}\n"
            f"work_mem = {wm}\n"
            f"maintenance_work_mem = {mwm}\n"
            f"huge_pages = {self._huge_pages()}\n\n"
            f"# ── Connections ──────────────────────────────────────────────\n"
            f"max_connections = {inp.max_connections}\n\n"
            f"# ── WAL / Checkpoints ────────────────────────────────────────\n"
            f"wal_buffers = {wb}\n"
            f"max_wal_size = {mws}GB\n"
            f"min_wal_size = 1GB\n"
            f"checkpoint_completion_target = 0.9\n"
            f"wal_compression = on\n\n"
            f"# ── Planner ──────────────────────────────────────────────────\n"
            f"random_page_cost = {rpc}\n"
            f"effective_io_concurrency = {eio}\n"
            f"default_statistics_target = {dst}\n\n"
            f"# ── Parallelism ────────────────────────────────────────────\n"
            f"max_worker_processes = {mwp}\n"
            f"max_parallel_workers = {mpw}\n"
            f"max_parallel_workers_per_gather = {mpwg}\n"
            f"max_parallel_maintenance_workers = {max(2, mpwg)}\n\n"
            f"# ── Autovacuum ───────────────────────────────────────────────\n"
            f"autovacuum = on\n"
            f"autovacuum_max_workers = 3\n"
            f"autovacuum_vacuum_scale_factor = 0.1\n"
            f"autovacuum_analyze_scale_factor = 0.05\n\n"
            f"# ── Logging ────────────────────────────────────────────────\n"
            f"log_min_duration_statement = 1000\n"
            f"log_checkpoints = on\n"
            f"log_connections = on\n"
            f"log_disconnections = on\n"
            f"log_lock_waits = on\n"
            f"log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '\n\n"
            f"# ── Security ───────────────────────────────────────────────\n"
            f"ssl = on\n"
            f"password_encryption = scram-sha-256\n"
            f"shared_preload_libraries = 'pg_stat_statements'\n"
            f"pg_stat_statements.track = all\n"
            f"{repl_block}"
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> PostgreSQLOutput:
        sb  = self._shared_buffers_mb()
        ecs = self._effective_cache_size_mb()
        wm  = self._work_mem_mb()
        mwm = self._maintenance_work_mem_mb()
        wb  = self._wal_buffers_mb()
        mws = self._max_wal_size_gb()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = self.inp.max_connections,
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            "Use streaming replication with at least one synchronous standby for HA.",
            "Deploy PgBouncer for connection pooling (transaction mode recommended for OLTP).",
            "Configure pg_basebackup for automated standby provisioning.",
            "Use Patroni + etcd for automatic failover in Kubernetes/VM environments.",
            "Enable WAL archiving for point-in-time recovery: archive_mode=on.",
        ]

        perf_warnings = [w for w in [
            (f"max_connections={self.inp.max_connections} is high. Each connection uses ~10MB RAM. "
             "Consider PgBouncer for connection pooling.")
            if self.inp.max_connections > 300 else None,

            ("workload_type=olap but max_connections>100. OLAP queries are resource-intensive. "
             "Reduce max_connections and increase work_mem.")
            if self.inp.workload_type in ("olap", "data_warehouse") and self.inp.max_connections > 100 else None,

            (f"storage_type=hdd. PostgreSQL performance is dramatically limited by disk IOPS. "
             "Migrate to SSD for 10-50× improvement in random read performance.")
            if self.inp.storage_type == "hdd" else None,
        ] if w]

        return PostgreSQLOutput(
            mode                       = self.inp.mode,
            shared_buffers             = self._fmt_mem(sb),
            effective_cache_size       = self._fmt_mem(ecs),
            work_mem                   = self._fmt_mem(wm),
            maintenance_work_mem       = self._fmt_mem(mwm),
            recommended_max_connections = self.inp.max_connections,
            wal_buffers                = self._fmt_mem(wb),
            max_wal_size               = f"{mws}GB",
            postgresql_conf_snippet    = self._render_conf(),
            major_params               = major,
            medium_params              = medium,
            minor_params               = minor,
            os_sysctl_conf             = os_engine.sysctl_block(),
            ha_suggestions             = ha_suggestions,
            performance_warnings       = perf_warnings,
            capacity_warning           = self._capacity_warning(
                self.inp.max_connections * 10, self.inp.ram_gb * 1024,
                "PostgreSQL connection memory"
            ),
            audit_findings             = self._audit()
                                         if self.inp.mode == CalcMode.EXISTING else [],
        )
