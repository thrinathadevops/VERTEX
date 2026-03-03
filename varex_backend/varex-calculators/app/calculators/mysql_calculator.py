"""
app/calculators/mysql_calculator.py
====================================
MySQL/MariaDB tuning calculator — NEW and EXISTING modes.

InnoDB memory formula (MySQL docs + Percona best practices)
-----------------------------------------------------------
innodb_buffer_pool_size = RAM × 70% (dedicated) or RAM × 50% (shared)
innodb_buffer_pool_instances = min(buffer_pool_size_GB, 64)
innodb_log_file_size   = max(256MB, buffer_pool_size / 4), capped at 2GB
innodb_io_capacity     = 200 (HDD) / 2000 (SSD) / 10000 (NVMe)
max_connections        = user-specified (default 200)
thread_pool_size       = cpu_cores
table_open_cache       = max_connections × 2
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.mysql import MySQLInput, MySQLOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class MySQLCalculator(BaseCalculator):

    def __init__(self, inp: MySQLInput) -> None:
        self._require_positive(inp.cpu_cores,       "cpu_cores")
        self._require_positive(inp.ram_gb,           "ram_gb")
        self._require_positive(inp.max_connections,  "max_connections")
        self.inp = inp

    # ── internal calculations ─────────────────────────────────────────────────

    def _buffer_pool_gb(self) -> float:
        ratio = 0.80 if self.inp.dedicated else 0.50
        return round(self.inp.ram_gb * ratio, 1)

    def _buffer_pool_instances(self) -> int:
        gb = self._buffer_pool_gb()
        return max(1, min(int(gb), 64))

    def _log_file_size_mb(self) -> int:
        bp_mb = int(self._buffer_pool_gb() * 1024)
        return max(256, min(bp_mb // 4, 2048))

    def _io_capacity(self) -> int:
        if self.inp.storage_type == "nvme":
            return 10000
        if self.inp.storage_type == "ssd":
            return 2000
        return 200

    def _io_capacity_max(self) -> int:
        return self._io_capacity() * 2

    def _thread_pool_size(self) -> int:
        return self.inp.cpu_cores

    def _table_open_cache(self) -> int:
        return max(2000, self.inp.max_connections * 2)

    def _tmp_table_size_mb(self) -> int:
        return max(64, min(int(self.inp.ram_gb * 1024 * 0.01), 256))

    @staticmethod
    def _fmt_mem_gb(gb: float) -> str:
        if gb == int(gb):
            return f"{int(gb)}G"
        return f"{gb}G"

    @staticmethod
    def _fmt_mem_mb(mb: int) -> str:
        if mb >= 1024 and mb % 1024 == 0:
            return f"{mb // 1024}G"
        return f"{mb}M"

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        bp   = self._buffer_pool_gb()
        bpi  = self._buffer_pool_instances()
        lfs  = self._log_file_size_mb()
        ioc  = self._io_capacity()
        iocm = self._io_capacity_max()
        tps  = self._thread_pool_size()
        toc  = self._table_open_cache()
        tmp  = self._tmp_table_size_mb()

        params = [
            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "innodb_buffer_pool_size", self._fmt_mem_gb(bp), M,
                f"InnoDB buffer pool = {'80%' if inp.dedicated else '50%'} of RAM = {self._fmt_mem_gb(bp)}. "
                f"Default 128MB is catastrophically low. The buffer pool caches data AND indexes. "
                "A larger pool means fewer disk reads. For dedicated MySQL: 70-80% of RAM is optimal. "
                "Remaining 20% covers OS, threads, tmp tables, and connection overhead.",
                f"innodb_buffer_pool_size = {self._fmt_mem_gb(bp)}",
                ex.innodb_buffer_pool_size,
                safe=False,
            ),
            p(
                "innodb_buffer_pool_instances", str(bpi), M,
                f"Buffer pool split into {bpi} instances for reduced mutex contention. "
                f"Formula: min(buffer_pool_size_GB, 64) = min({int(bp)}, 64). "
                "Each instance has its own LRU list and free list. "
                "With 1 instance: all threads compete for one mutex → lock contention under load.",
                f"innodb_buffer_pool_instances = {bpi}",
                str(ex.innodb_buffer_pool_instances) if ex.innodb_buffer_pool_instances else None,
                safe=False,
            ),
            p(
                "innodb_log_file_size", self._fmt_mem_mb(lfs), M,
                f"InnoDB redo log file size = {self._fmt_mem_mb(lfs)}. "
                f"Formula: max(256MB, buffer_pool / 4) = max(256MB, {int(bp*1024)}MB/4). "
                "Larger logs reduce checkpoint frequency → smoother I/O. "
                "Too small → aggressive checkpointing → write stalls. "
                "Recovery time ≈ log_size / disk_throughput.",
                f"innodb_log_file_size = {self._fmt_mem_mb(lfs)}",
                ex.innodb_log_file_size,
                safe=False,
            ),
            p(
                "innodb_flush_log_at_trx_commit", "1", M,
                "Controls ACID durability guarantee. "
                "1 = full ACID (flush after every commit) — required for financial/critical data. "
                "2 = flush to OS buffer every commit, fsync once/sec — safe if OS doesn't crash. "
                "0 = fsync once/sec — fastest, up to 1 second data loss on crash. "
                "Default=1 is correct for production.",
                "innodb_flush_log_at_trx_commit = 1",
                str(ex.innodb_flush_log_at_trx_commit) if ex.innodb_flush_log_at_trx_commit is not None else None,
            ),
            p(
                "max_connections", str(inp.max_connections), M,
                f"Maximum concurrent connections = {inp.max_connections}. "
                "Each connection uses ~1MB RAM (thread stack + sort/join buffers). "
                "Use ProxySQL or MySQL Router for connection pooling if >500 connections needed.",
                f"max_connections = {inp.max_connections}",
                str(ex.max_connections) if ex.max_connections else None,
                safe=False,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "innodb_io_capacity", str(ioc), MED,
                f"Background I/O operations per second = {ioc}. "
                f"{'HDD: 200 (based on ~200 IOPS).' if ioc == 200 else f'{inp.storage_type.upper()}: {ioc}.'} "
                "Controls dirty page flushing and change buffer merging rate. "
                "Too low on fast storage → dirty page backlog → write stalls.",
                f"innodb_io_capacity = {ioc}\ninnodb_io_capacity_max = {iocm}",
                str(ex.innodb_io_capacity) if ex.innodb_io_capacity else None,
            ),
            p(
                "table_open_cache", str(toc), MED,
                f"Open table cache = max_connections × 2 = {toc}. "
                "Each connection needing a table opens a file descriptor. "
                "Cache miss → open() syscall → latency spike.",
                f"table_open_cache = {toc}\ntable_open_cache_instances = 16",
                str(ex.table_open_cache) if ex.table_open_cache else None,
            ),
            p(
                "tmp_table_size + max_heap_table_size", self._fmt_mem_mb(tmp), MED,
                f"In-memory temp table limit = {self._fmt_mem_mb(tmp)}. "
                "Queries exceeding this spill to disk (dramatically slower). "
                "Both settings must match — the lower one wins.",
                f"tmp_table_size = {self._fmt_mem_mb(tmp)}\nmax_heap_table_size = {self._fmt_mem_mb(tmp)}",
                ex.tmp_table_size,
            ),
            p(
                "innodb_file_per_table", "ON", MED,
                "Store each InnoDB table in its own .ibd file instead of shared tablespace. "
                "Without this: DROP TABLE doesn't reclaim disk space. "
                "Default ON since MySQL 5.6.",
                "innodb_file_per_table = ON",
            ),
            p(
                "innodb_flush_method", "O_DIRECT", MED,
                "Bypass OS page cache for InnoDB data files. "
                "Avoids double-buffering (data in InnoDB buffer pool AND OS page cache). "
                "Mandatory for Linux with large buffer pools.",
                "innodb_flush_method = O_DIRECT",
            ),
            p(
                "binlog_format", "ROW", MED,
                "Row-based replication format. "
                "STATEMENT: can cause replication drift with non-deterministic functions. "
                "ROW: deterministic, larger binlogs but safe. "
                "MIXED: auto-switch (unpredictable). ROW is the MySQL 8.0+ default.",
                "binlog_format = ROW" + (
                    "\nlog_bin = mysql-bin\nserver_id = 1\n"
                    "binlog_expire_logs_seconds = 604800  # 7 days"
                    if inp.replication else ""
                ),
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "slow_query_log", "ON", MIN,
                "Log queries exceeding long_query_time. Essential for performance analysis.",
                "slow_query_log = ON\nlong_query_time = 1\nlog_slow_extra = ON",
            ),
            p(
                "performance_schema", "ON", MIN,
                "MySQL's built-in profiling. Overhead: 5-10% CPU. "
                "Without it: zero visibility into wait events, lock contention, I/O latency.",
                "performance_schema = ON",
            ),
            p(
                "innodb_print_all_deadlocks", "ON", MIN,
                "Log all deadlocks to error log. Default OFF only shows latest via SHOW ENGINE STATUS.",
                "innodb_print_all_deadlocks = ON",
            ),
            p(
                "skip_name_resolve", "ON", MIN,
                "Disable DNS lookups for client connections. "
                "DNS timeouts can cause connection delays of up to 30s.",
                "skip_name_resolve = ON",
                safe=False,
            ),
        ]

        return [x for x in params if x is not None]

    # ── audit ─────────────────────────────────────────────────────────────────

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing
        bp = self._buffer_pool_gb()

        if ex.innodb_buffer_pool_instances is not None and ex.innodb_buffer_pool_instances <= 1 and bp > 1:
            findings.append(
                f"[MAJOR] innodb_buffer_pool_instances=1 with {self._fmt_mem_gb(bp)} buffer pool. "
                f"Set to {self._buffer_pool_instances()} to reduce mutex contention."
            )
        if ex.innodb_io_capacity is not None and ex.innodb_io_capacity <= 200 and self.inp.storage_type != "hdd":
            findings.append(
                f"[MAJOR] innodb_io_capacity={ex.innodb_io_capacity} on {self.inp.storage_type}. "
                f"Set to {self._io_capacity()} — dirty page flushing is throttled."
            )
        if ex.query_cache_type is not None and ex.query_cache_type > 0:
            findings.append(
                "[MAJOR] query_cache_type is enabled. The query cache is removed in MySQL 8.0+ "
                "and was a known bottleneck due to global mutex. Disable immediately."
            )
        if not ex.binlog_enabled and self.inp.replication:
            findings.append(
                "[MAJOR] Binary logging disabled but replication requested. "
                "Replication requires log_bin=ON."
            )
        if not ex.ssl_enabled:
            findings.append(
                "[MEDIUM] SSL disabled. Client connections transmit data in plaintext."
            )

        return findings

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self) -> str:
        inp  = self.inp
        bp   = self._fmt_mem_gb(self._buffer_pool_gb())
        bpi  = self._buffer_pool_instances()
        lfs  = self._fmt_mem_mb(self._log_file_size_mb())
        ioc  = self._io_capacity()
        toc  = self._table_open_cache()
        tmp  = self._fmt_mem_mb(self._tmp_table_size_mb())

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗\n"
            f"# ║  VAREX my.cnf  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}              ║\n"
            f"# ╚══════════════════════════════════════════════════════════════╝\n\n"
            f"[mysqld]\n\n"
            f"# ── InnoDB Engine ────────────────────────────────────────────\n"
            f"innodb_buffer_pool_size = {bp}\n"
            f"innodb_buffer_pool_instances = {bpi}\n"
            f"innodb_log_file_size = {lfs}\n"
            f"innodb_flush_log_at_trx_commit = 1\n"
            f"innodb_flush_method = O_DIRECT\n"
            f"innodb_file_per_table = ON\n"
            f"innodb_io_capacity = {ioc}\n"
            f"innodb_io_capacity_max = {ioc * 2}\n"
            f"innodb_print_all_deadlocks = ON\n\n"
            f"# ── Connections ──────────────────────────────────────────────\n"
            f"max_connections = {inp.max_connections}\n"
            f"table_open_cache = {toc}\n"
            f"table_open_cache_instances = 16\n"
            f"skip_name_resolve = ON\n\n"
            f"# ── Memory ───────────────────────────────────────────────────\n"
            f"tmp_table_size = {tmp}\n"
            f"max_heap_table_size = {tmp}\n\n"
            f"# ── Replication ──────────────────────────────────────────────\n"
            + (f"log_bin = mysql-bin\n"
               f"server_id = 1\n"
               f"binlog_format = ROW\n"
               f"binlog_expire_logs_seconds = 604800\n"
               f"gtid_mode = ON\n"
               f"enforce_gtid_consistency = ON\n"
               if inp.replication else "# log_bin = OFF\n") +
            f"\n# ── Logging ────────────────────────────────────────────────\n"
            f"slow_query_log = ON\n"
            f"long_query_time = 1\n"
            f"log_slow_extra = ON\n"
            f"performance_schema = ON\n"
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> MySQLOutput:
        bp  = self._buffer_pool_gb()
        bpi = self._buffer_pool_instances()
        lfs = self._log_file_size_mb()
        ioc = self._io_capacity()

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
            "Use MySQL InnoDB Cluster (Group Replication) for HA with automatic failover.",
            "Deploy ProxySQL for connection pooling and read/write splitting.",
            "Enable GTID-based replication for easier failover management.",
            "Use MySQL Router for transparent routing between primary and replicas.",
            "Configure semi-synchronous replication for zero-data-loss failover.",
        ]

        perf_warnings = [w for w in [
            (f"max_connections={self.inp.max_connections} is high. Use ProxySQL for pooling.")
            if self.inp.max_connections > 500 else None,

            (f"storage_type=hdd. InnoDB random I/O is severely limited on HDD. Migrate to SSD.")
            if self.inp.storage_type == "hdd" else None,
        ] if w]

        return MySQLOutput(
            mode                         = self.inp.mode,
            innodb_buffer_pool_size      = self._fmt_mem_gb(bp),
            innodb_buffer_pool_instances = bpi,
            innodb_log_file_size         = self._fmt_mem_mb(lfs),
            innodb_io_capacity           = ioc,
            recommended_max_connections  = self.inp.max_connections,
            my_cnf_snippet               = self._render_conf(),
            major_params                 = major,
            medium_params                = medium,
            minor_params                 = minor,
            os_sysctl_conf               = os_engine.sysctl_block(),
            ha_suggestions               = ha_suggestions,
            performance_warnings         = perf_warnings,
            capacity_warning             = self._capacity_warning(
                self.inp.max_connections, 10000, "MySQL connections"
            ),
            audit_findings               = self._audit()
                                           if self.inp.mode == CalcMode.EXISTING else [],
        )
