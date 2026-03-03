"""
app/calculators/redis_calculator.py
=====================================
Redis tuning calculator — NEW and EXISTING modes.

Memory reservation formula
--------------------------
reserved_ratio = base_os_overhead
               + fragmentation_headroom
               + replication_cow          (if replication=True)
               + aof_rewrite_buffer       (if "aof" in persistence)

Where:
  base_os_overhead      = 0.20  (OS kernel + jemalloc allocator overhead)
  fragmentation_headroom= 0.10  (jemalloc fragmentation ratio ~1.1 = 10%)
  replication_cow       = 0.10  (BGSAVE fork copy-on-write dirty pages)
  aof_rewrite_buffer    = 0.05  (AOF rewrite buffer accumulation during rewrite)
  max reserved_ratio    = 0.50  (never give more than 50% to overhead)

maxmemory = RAM × (1 - reserved_ratio)

Dataset size formula
--------------------
estimated_dataset_gb = avg_key_size_kb × estimated_keys / (1024 × 1024)

Eviction policy selection
-------------------------
"aof" in persistence → volatile-lru  (protect TTL-less keys from eviction)
otherwise            → allkeys-lru   (pure cache: evict any LRU key)
"""
from __future__ import annotations

from app.varex_calculators.calculators.base import BaseCalculator
from app.varex_calculators.calculators.os_tuning import OSTuningEngine
from app.varex_calculators.core.enums import ImpactLevel, CalcMode
from app.varex_calculators.schemas.redis import RedisInput, RedisOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class RedisCalculator(BaseCalculator):

    def __init__(self, inp: RedisInput) -> None:
        self._require_positive(inp.ram_gb,          "ram_gb")
        self._require_positive(inp.avg_key_size_kb, "avg_key_size_kb")
        self._require_positive(inp.estimated_keys,  "estimated_keys")
        self.inp = inp

    # ── internal calculations ─────────────────────────────────────────────────

    def _dataset_gb(self) -> float:
        """
        Estimated in-memory dataset size (GB).
        Formula: avg_key_size_kb × estimated_keys / (1024 * 1024)
        Does NOT include Redis metadata overhead (~50 bytes per key).
        Add ~5% for per-key dict/ziplist/listpack struct overhead.
        """
        raw = self.inp.avg_key_size_kb * self.inp.estimated_keys / (1024 * 1024)
        return round(raw * 1.05, 4)  # +5% key metadata

    def _reserved_ratio(self) -> float:
        """
        Fraction of RAM that must NOT be given to maxmemory.

        Component breakdown:
          0.20 — OS + jemalloc allocator baseline overhead
          0.10 — jemalloc fragmentation (fragmentation_ratio ~1.1 under load)
          0.10 — COW dirty pages during BGSAVE fork (replication/RDB)
          0.05 — AOF rewrite buffer (accumulates writes during rewrite)
        """
        ratio = 0.20 + 0.10  # OS overhead + fragmentation always present
        if self.inp.replication or "rdb" in self.inp.persistence:
            ratio += 0.10     # BGSAVE fork COW reservation
        if "aof" in self.inp.persistence:
            ratio += 0.05     # AOF rewrite buffer
        return min(ratio, 0.50)

    def _reserved_breakdown(self) -> str:
        """Human-readable breakdown of the reserved_ratio."""
        parts = ["20% OS+jemalloc baseline", "10% fragmentation headroom"]
        if self.inp.replication or "rdb" in self.inp.persistence:
            parts.append("10% BGSAVE fork COW")
        if "aof" in self.inp.persistence:
            parts.append("5% AOF rewrite buffer")
        total = int(self._reserved_ratio() * 100)
        return f"{total}% total = " + " + ".join(parts)

    def _maxmemory_gb(self) -> float:
        return round(self.inp.ram_gb * (1 - self._reserved_ratio()), 2)

    def _reserved_gb(self) -> float:
        return round(self.inp.ram_gb * self._reserved_ratio(), 2)

    def _eviction_policy(self) -> str:
        """
        volatile-lru: evict only keys with TTL set (protects permanent keys).
                      Best for mixed workloads (some keys have TTL, some don't).
        allkeys-lru:  evict any key regardless of TTL.
                      Best for pure cache workloads (all keys are expendable).
        noeviction:   return write error when full — only for primary data stores
                      where data loss is unacceptable and OOM is preferable.
        """
        if "aof" in self.inp.persistence and self.inp.persistence != "none":
            return "volatile-lru"
        return "allkeys-lru"

    def _maxclients(self) -> int:
        """
        Recommended maxclients.
        Formula: min(peak_ops_per_sec * 2, 10000)
        Redis is single-threaded per command — more clients than needed
        just consume memory and FD count.
        """
        return min(self.inp.peak_ops_per_sec * 2, 10_000)

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self, mm: float, rg: float) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        res  = self._reserved_breakdown()
        pol  = self._eviction_policy()
        mc   = self._maxclients()

        params = [

            # ── MAJOR: memory / security / persistence ────────────────────
            p(
                "maxmemory", f"{mm}gb", M,
                f"Hard memory ceiling = RAM({inp.ram_gb}GB) × (1 - reserved_ratio) = {mm}GB. "
                f"Reserved {rg}GB ({res}). "
                "Without maxmemory: Redis grows unbounded until the OS OOM-killer terminates it. "
                "OOM-kill of Redis during peak traffic = complete service outage. "
                "NEVER leave maxmemory unset on a shared host.",
                f"maxmemory {mm}gb",
                f"{ex.maxmemory_gb}gb" if ex.maxmemory_gb else None,
                safe=False,
            ),
            p(
                "maxmemory-policy", pol, M,
                f"What Redis does when maxmemory is reached. Recommended: {pol}. "
                "noeviction (default): all writes return OOM error — application crashes. "
                "allkeys-lru: evict least-recently-used key (correct for pure caches). "
                "volatile-lru: evict only TTL-set keys (correct for mixed TTL+persistent). "
                "allkeys-lfu: evict least-frequently-used (better than LRU for skewed access). "
                f"Your persistence={inp.persistence} → {pol} is correct.",
                f"maxmemory-policy {pol}",
                ex.maxmemory_policy,
            ),
            p(
                "requirepass", "<strong-password>", M,
                "Default Redis has NO authentication. Any process or user on the network "
                "with TCP access to port 6379 has full read/write/delete access to ALL data. "
                "Shodan scans show ~20,000 unauthenticated Redis instances exposed publicly. "
                "Redis 6+: prefer ACL SETUSER for fine-grained per-user permissions. "
                "Minimum: 32-character random password.",
                "requirepass YourStrongPasswordHere
"
                "# Redis 6+ ACL alternative:
"
                "# ACL SETUSER appuser on >StrongPass123 ~* &* +@all -@dangerous",
                "SET" if ex.requirepass_set else "NOT SET",
            ),
            p(
                "bind", "127.0.0.1 -::1", M,
                "Default bind 0.0.0.0 exposes Redis on ALL interfaces including public NICs. "
                "Bind ONLY to loopback (127.0.0.1) or specific private LAN IP. "
                "For Redis Cluster: bind to the private replication IP, not 0.0.0.0. "
                "Combining bind=127.0.0.1 + requirepass + protected-mode=yes = "
                "defence-in-depth against network exposure.",
                "bind 127.0.0.1 -::1
"
                "# For cluster node with private IP:
"
                "# bind 10.0.0.5 127.0.0.1",
                ex.bind,
            ),
            p(
                "appendonly",
                "yes" if "aof" in inp.persistence else "no",
                M,
                "AOF (Append-Only File): logs every write command to disk. "
                "Survives crashes with maximum 1 second of data loss (appendfsync=everysec). "
                "RDB-only: risk losing up to save-interval minutes of writes (default: 15min). "
                f"Your persistence={inp.persistence} → "
                f"appendonly={'yes' if 'aof' in inp.persistence else 'no'}. "
                "rdb+aof: AOF used on restart (more complete), RDB kept for backup and replication.",
                f"appendonly {'yes' if 'aof' in inp.persistence else 'no'}",
                ex.appendonly,
                safe=False,
            ),
            p(
                'rename-command FLUSHALL ""', '"" (disabled)', M,
                "FLUSHALL deletes ALL keys in ALL databases in <1ms with no confirmation. "
                "FLUSHDB deletes all keys in the current database. "
                "CONFIG allows remote reconfiguration (changing bind, requirepass at runtime). "
                "DEBUG can crash or corrupt Redis. "
                "Renaming to empty string disables the command entirely. "
                "Use ACL SETUSER to allow only trusted admin users to run these commands.",
                'rename-command FLUSHALL ""
'
                'rename-command FLUSHDB ""
'
                'rename-command CONFIG  ""
'
                'rename-command DEBUG   ""
'
                'rename-command KEYS    ""  # KEYS * is O(N) and blocks the event loop',
            ),
            p(
                "protected-mode", "yes", M,
                "protected-mode=yes blocks all remote connections when no bind address "
                "AND no requirepass is configured. This is Redis's last-resort safety net. "
                "Do NOT set to no unless both bind (restricted IP) and requirepass are set. "
                "protected-mode=no + no requirepass = completely open Redis.",
                "protected-mode yes",
                ex.protected_mode,
            ),
            p(
                "maxclients", str(mc), M,
                f"Maximum simultaneous client connections = {mc}. "
                f"Formula: min(peak_ops_per_sec×2, 10000) = min({inp.peak_ops_per_sec*2}, 10000). "
                "Redis is single-threaded: more clients than needed just consume "
                "memory (~20KB per client) and OS file descriptors. "
                "Default 10000 is usually fine unless you have connection pool leaks.",
                f"maxclients {mc}",
                str(ex.maxclients) if ex.maxclients else None,
            ),

            # ── MEDIUM: performance / persistence tuning ──────────────────
            p(
                "appendfsync", "everysec", MED,
                "Controls how often AOF buffer is flushed to disk. "
                "always:   fsync after every write command = maximum durability, "
                "          ~50% write throughput reduction (each write blocks on disk I/O). "
                "everysec: fsync once per second = maximum 1 second data loss, "
                "          near-native throughput (background thread does the fsync). "
                "no:       OS decides when to flush = fastest, but may lose minutes of data. "
                "Production standard: everysec.",
                "appendfsync everysec",
            ),
            p(
                "hz", "15", MED,
                "Event loop frequency in ticks per second. Default=10. "
                "Affects: key expiry precision, client connection timeout checks, "
                "background tasks (LRU sampling, cluster gossip). "
                "At hz=10: expired keys may linger for up to 100ms before expiry. "
                "At hz=15: max expiry lag = 67ms with <1% additional CPU overhead. "
                "dynamic-hz allows scaling up to 500 ticks/sec under heavy load.",
                "hz 15
dynamic-hz yes",
                str(ex.hz) if ex.hz else None,
            ),
            p(
                "lazyfree-lazy-eviction", "yes", MED,
                "Perform eviction, expiry, and deletion in BIO (Background I/O) threads "
                "instead of the main event loop thread. "
                "Without lazyfree: deleting a 1GB list/set blocks the main thread "
                "for 100ms–2s, causing latency spikes for ALL other clients. "
                "Critical for workloads with large values (>1MB) or bulk key deletions. "
                "Redis 4+ feature — always enable in production.",
                "lazyfree-lazy-eviction  yes
"
                "lazyfree-lazy-expire    yes
"
                "lazyfree-lazy-server-del yes
"
                "replica-lazy-flush      yes",
            ),
            p(
                "tcp-backlog", "511", MED,
                "TCP accept queue depth for the Redis listen socket. "
                "Must be ≤ net.core.somaxconn (OS hard ceiling). "
                "Default 511. Verify with: sudo ss -lnt | grep 6379 — "
                "the 'Recv-Q' column shows current queue depth. "
                "Overflow causes immediate connection-refused even with available capacity.",
                "tcp-backlog 511",
                str(ex.tcp_backlog) if ex.tcp_backlog else None,
            ),
            p(
                "timeout", "300", MED,
                "Close idle client connections after 300 seconds. "
                "Default=0 means connections NEVER close automatically. "
                "Idle connections accumulate: each consumes ~20KB memory + 1 FD. "
                "With maxclients=10000 and timeout=0: connection pool leaks silently "
                "exhaust all available client slots.",
                "timeout 300",
                str(ex.timeout) if ex.timeout else None,
            ),
            p(
                "maxmemory-samples", "10", MED,
                "Number of keys sampled for LRU approximation. "
                "Redis uses approximate LRU (not exact) to avoid O(N) full scan. "
                "Default=5: ~10% accuracy loss vs true LRU (may evict recently-used keys). "
                "samples=10: <2% accuracy loss, negligible CPU overhead (<0.5%). "
                "samples=20: near-perfect LRU accuracy, ~1% CPU overhead.",
                "maxmemory-samples 10",
            ),
            p(
                "save intervals",
                "900 1 / 300 10 / 60 10000" if "rdb" in inp.persistence else "disabled",
                MED,
                "RDB snapshot trigger conditions. Multiple triggers use OR logic. "
                "Default 900 1 (snapshot after 15min with 1 change) is too infrequent "
                "for active datasets — risks 15 minutes of data loss. "
                "60 10000: snapshot if 10K changes in 60s = balanced I/O vs data safety. "
                f"{'RDB disabled because persistence=' + inp.persistence if inp.persistence == 'none' else ''}",
                "save 900 1
save 300 10
save 60 10000"
                if "rdb" in inp.persistence else "# RDB disabled
# save ''",
            ),
            p(
                "active-expire-enabled", "1", MED,
                "Background active key expiry. Without this, expired keys are only removed "
                "when accessed (lazy expiry). Active expiry proactively reclaims memory from "
                "unused expired keys, preventing memory bloat in workloads with high TTL usage.",
                "active-expire-enabled 1
active-expire-effort  1",
            ),
            p(
                "aof-use-rdb-preamble", "yes", MED,
                "Write RDB snapshot as AOF file preamble on rewrite. "
                "Dramatically reduces AOF rewrite time and AOF file size. "
                "On restart: load RDB preamble (fast binary format) then replay "
                "only the delta AOF commands. Best of both formats.",
                "aof-use-rdb-preamble yes",
            ) if "aof" in inp.persistence else None,
            p(
                "aof-rewrite-incremental-fsync", "yes", MED,
                "Fsync AOF file in 4MB chunks during rewrite instead of one large fsync. "
                "Without this, AOF rewrite causes a single multi-second fsync stall "
                "that can block the main thread.",
                "aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync    yes",
            ) if "aof" in inp.persistence else None,

            # ── MINOR: observability / hardening ─────────────────────────
            p(
                "latency-monitor-threshold", "50", MIN,
                "Log all operations that take >50ms. Essential for identifying: "
                "slow Lua scripts, large key operations (LRANGE on 1M-element list), "
                "BGSAVE latency, AOF rewrite stalls. "
                "Monitor with: redis-cli LATENCY LATEST / LATENCY HISTORY event.",
                "latency-monitor-threshold 50",
            ),
            p(
                "slowlog-log-slower-than", "10000", MIN,
                "Log commands taking >10ms (10000 microseconds). "
                "Common culprits: KEYS * (O(N)), SORT, SMEMBERS on large sets, "
                "Lua EVAL with loops. Monitor with: SLOWLOG GET 25.",
                "slowlog-log-slower-than 10000
slowlog-max-len         256",
            ),
            p(
                "activerehashing", "yes", MIN,
                "Incremental hash table rehashing during CPU-idle cycles between commands. "
                "Without this, when a hash table needs doubling, Redis does it in one "
                "blocking operation causing a latency spike.",
                "activerehashing yes",
            ),
            p(
                "loglevel", "notice", MIN,
                "debug/verbose log levels generate massive I/O at >10K OPS. "
                "notice logs important events only — correct for production.",
                "loglevel notice",
            ),
            p(
                "tcp-keepalive", "300", MIN,
                "Send TCP keepalive probes every 300s. "
                "Detects dead client connections (network failure, crash) and frees FDs. "
                "Prevents stale connections accumulating in CLOSE_WAIT state.",
                "tcp-keepalive 300",
            ),
            p(
                "crash-log-enabled", "yes", MIN,
                "Write crash log on fatal errors. Essential for post-mortem analysis. "
                "Crash logs include stack trace, memory stats, and last commands.",
                "crash-log-enabled yes
crash-memlog-enabled yes",
            ),
            p(
                "repl-diskless-sync", "yes", MIN,
                "Stream RDB directly to replica over socket instead of writing to disk first. "
                "Avoids temporary disk space requirement for large datasets. "
                "Beneficial when disk I/O is the bottleneck (cloud VMs with slow EBS).",
            ) if inp.replication else None,
        ]

        return [x for x in params if x is not None]

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self, mm: float) -> list[str]:
        findings = []
        ex = self.inp

        if ex.existing.maxmemory_policy == "noeviction":
            findings.append(
                f"[MAJOR] maxmemory-policy=noeviction → ALL write commands return OOM errors "
                f"when memory is full. Change to {self._eviction_policy()} immediately."
            )
        if not ex.existing.requirepass_set:
            findings.append(
                "[MAJOR] requirepass NOT SET. Redis is completely unauthenticated. "
                "Any process with network access to port 6379 has full admin access."
            )
        if ex.existing.protected_mode == "no" and not ex.existing.requirepass_set:
            findings.append(
                "[MAJOR] protected-mode=no AND requirepass not set. "
                "Redis accepts connections from any remote host with zero authentication."
            )
        if ex.existing.bind and "0.0.0.0" in ex.existing.bind:
            findings.append(
                "[MAJOR] bind=0.0.0.0 exposes Redis on ALL network interfaces including "
                "public NICs. Restrict to 127.0.0.1 or internal LAN IP."
            )
        if ex.existing.maxmemory_gb and ex.existing.maxmemory_gb > mm:
            findings.append(
                f"[MAJOR] maxmemory={ex.existing.maxmemory_gb}GB leaves only "
                f"{round(self.inp.ram_gb - ex.existing.maxmemory_gb, 2)}GB for OS + fragmentation. "
                f"Recommended maxmemory: {mm}GB."
            )
        if ex.existing.appendonly == "no" and "aof" in self.inp.persistence:
            findings.append(
                "[MAJOR] appendonly=no but AOF persistence requested. "
                "Data is NOT being written to AOF — persistence is silently disabled."
            )
        if ex.existing.hz and ex.existing.hz < 10:
            findings.append(
                f"[MEDIUM] hz={ex.existing.hz}. Key expiry and background jobs lag "
                f"by {int(1000/ex.existing.hz)}ms+. Increase to 15."
            )
        if ex.existing.timeout == 0 or ex.existing.timeout is None:
            findings.append(
                "[MEDIUM] timeout=0. Idle connections never close. "
                "Connection pool leaks silently exhaust maxclients."
            )
        if ex.existing.maxclients and ex.existing.maxclients > 50000:
            findings.append(
                f"[MEDIUM] maxclients={ex.existing.maxclients} is very high. "
                "Each idle client consumes ~20KB RAM + 1 FD. "
                f"Recommended: {self._maxclients()}."
            )

        # OS-level audit
        for k, v in ex.existing.os_sysctl.items():
            try:
                if k == "vm.overcommit_memory" and v != "1":
                    findings.append(
                        f"[MAJOR] vm.overcommit_memory={v}. "
                        "Redis BGSAVE/BGREWRITEAOF fork() WILL fail with ENOMEM "
                        "under memory pressure. Set to 1 immediately."
                    )
                if k == "transparent_hugepage" and v in ("always", "madvise"):
                    findings.append(
                        f"[MAJOR] transparent_hugepage={v}. "
                        "Causes 2–10s latency spikes during every BGSAVE fork. "
                        "Set to never."
                    )
                if k == "net.core.somaxconn" and int(v) < 512:
                    findings.append(
                        f"[MEDIUM] net.core.somaxconn={v}. "
                        "Redis tcp-backlog is capped to this OS value. "
                        "Connection-refused under burst traffic."
                    )
                if k == "vm.swappiness" and int(v) > 10:
                    findings.append(
                        f"[MEDIUM] vm.swappiness={v}. "
                        "Redis keys being swapped to disk = 100x latency increase. "
                        "Set to 1 for Redis-only nodes."
                    )
            except ValueError:
                pass

        return findings

    # ── config renderer ───────────────────────────────────────────────────────

    def _render_conf(self, mm: float) -> str:
        inp = self.inp
        pol = self._eviction_policy()
        mc  = self._maxclients()

        save_block = (
            "save 900 1
save 300 10
save 60 10000"
            if "rdb" in inp.persistence else
            "# RDB disabled — comment out or remove all save lines
# save ''"
        )
        aof_block = (
            "appendonly             yes
"
            "appendfsync            everysec
"
            "aof-use-rdb-preamble   yes
"
            "aof-rewrite-incremental-fsync yes"
        ) if "aof" in inp.persistence else "appendonly no"

        repl_block = (
            "
# ── Replication ─────────────────────────────────────────────
"
            "repl-diskless-sync         yes
"
            "repl-diskless-sync-delay   5
"
            "min-replicas-to-write      1
"
            "min-replicas-max-lag       10
"
        ) if inp.replication else ""

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX redis.conf  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}          ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝

"
            f"# ── Network ──────────────────────────────────────────────────
"
            f"bind              127.0.0.1 -::1
"
            f"protected-mode    yes
"
            f"port              6379
"
            f"tcp-backlog       511
"
            f"tcp-keepalive     300
"
            f"timeout           300

"
            f"# ── Security ─────────────────────────────────────────────────
"
            f"requirepass       YourStrongPasswordHere
"
            f'rename-command FLUSHALL ""
'
            f'rename-command FLUSHDB  ""
'
            f'rename-command CONFIG   ""
'
            f'rename-command DEBUG    ""
'
            f'rename-command KEYS     ""

'
            f"# ── Memory ───────────────────────────────────────────────────
"
            f"maxmemory         {mm}gb
"
            f"maxmemory-policy  {pol}
"
            f"maxmemory-samples 10
"
            f"maxclients        {mc}
"
            f"activerehashing   yes
"
            f"active-expire-enabled  1
"
            f"active-expire-effort   1

"
            f"# ── Lazyfree ─────────────────────────────────────────────────
"
            f"lazyfree-lazy-eviction   yes
"
            f"lazyfree-lazy-expire     yes
"
            f"lazyfree-lazy-server-del yes
"
            f"replica-lazy-flush       yes

"
            f"# ── Persistence ──────────────────────────────────────────────
"
            f"{save_block}
"
            f"{aof_block}
"
            f"{repl_block}
"
            f"# ── Event loop ───────────────────────────────────────────────
"
            f"hz                15
"
            f"dynamic-hz        yes

"
            f"# ── Observability ────────────────────────────────────────────
"
            f"latency-monitor-threshold  50
"
            f"slowlog-log-slower-than    10000
"
            f"slowlog-max-len            256
"
            f"loglevel                   notice
"
            f"crash-log-enabled          yes
"
            f"crash-memlog-enabled       yes
"
        )

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> RedisOutput:
        ds = self._dataset_gb()
        mm = self._maxmemory_gb()
        rg = self._reserved_gb()

        all_params = self._build_params(mm, rg)

        # Append shared OS/kernel params (THP disabled — mandatory for Redis)
        os_engine = OSTuningEngine(
            cpu         = self.inp.cpu_cores,
            ram_gb      = self.inp.ram_gb,
            max_conns   = max(10_000, self.inp.peak_ops_per_sec),
            os_type     = self.inp.os_type,
            existing    = dict(self.inp.existing.os_sysctl),
            disable_thp = True,   # THP causes BGSAVE latency spikes
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            "Redis Sentinel (min 3 nodes: 1 primary + 1 replica + 1 sentinel) for automatic failover.",
            "Redis Cluster for horizontal sharding. "
            f"Shard formula: dataset_gb ({ds:.1f}GB) / maxmemory_per_node ({mm}GB) = "
            f"{max(1, int(ds/mm)+1)} shards minimum.",
            "Place replicas in separate AZs. Set min-replicas-to-write=1 min-replicas-max-lag=10.",
            "Enable TLS: redis-server --tls-port 6379 --tls-cert-file ... for in-transit encryption.",
            "Use Redis ACL (Redis 6+) for per-user permission scoping instead of shared requirepass.",
        ]
        if self.inp.cluster_nodes > 1:
            ha_suggestions.append(
                f"With {self.inp.cluster_nodes} nodes: run "
                "'redis-cli --cluster rebalance --cluster-use-empty-masters' after topology changes."
            )

        perf_warnings = [w for w in [
            (f"Estimated dataset ({ds:.2f}GB) > recommended maxmemory ({mm:.2f}GB). "
             "Data WILL be evicted. Add RAM or enable clustering.")
            if ds > mm else None,

            ("AOF + >100K OPS: monitor 'aof_delayed_fsync' in INFO stats. "
             "Consider appendfsync=no with external backup for ultra-high throughput.")
            if "aof" in self.inp.persistence and self.inp.peak_ops_per_sec > 100_000 else None,

            ("replication=True but cluster_nodes=1 means no replica is defined. "
             "Add at least 1 replica node for HA.")
            if self.inp.cluster_nodes == 1 and self.inp.replication else None,

            ("persistence=none: Redis is a pure cache. Restart = complete data loss. "
             "Ensure your application handles cold-cache gracefully.")
            if self.inp.persistence == "none" else None,
        ] if w]

        return RedisOutput(
            mode                      = self.inp.mode,
            estimated_dataset_gb      = ds,
            recommended_maxmemory_gb  = mm,
            maxmemory_reserved_gb     = rg,
            reserved_ratio_breakdown  = self._reserved_breakdown(),
            eviction_policy           = self._eviction_policy(),
            redis_conf_snippet        = self._render_conf(mm),
            major_params              = major,
            medium_params             = medium,
            minor_params              = minor,
            os_sysctl_conf            = os_engine.sysctl_block(),
            ha_suggestions            = ha_suggestions,
            performance_warnings      = perf_warnings,
            capacity_warning          = self._capacity_warning(
                ds, mm, "Redis maxmemory"
            ),
            audit_findings            = self._audit(mm)
                                        if self.inp.mode == CalcMode.EXISTING else [],
        )


