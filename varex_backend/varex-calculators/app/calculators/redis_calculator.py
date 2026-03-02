from __future__ import annotations
from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.core.models import TuningParam
from app.schemas.redis import RedisInput, RedisOutput

M, MED, MIN = ImpactLevel.MAJOR, ImpactLevel.MEDIUM, ImpactLevel.MINOR


class RedisCalculator(BaseCalculator):
    _BASE_RESERVED:   float = 0.20
    _FRAG_RESERVED:   float = 0.10
    _REPL_OVERHEAD:   float = 0.10
    _AOF_OVERHEAD:    float = 0.05

    def __init__(self, inp: RedisInput) -> None:
        self._require_positive(inp.ram_gb,          "ram_gb")
        self._require_positive(inp.avg_key_size_kb, "avg_key_size_kb")
        self._require_positive(inp.estimated_keys,  "estimated_keys")
        self.inp = inp

    def _dataset_gb(self) -> float:
        return round(self.inp.avg_key_size_kb * self.inp.estimated_keys / (1024 * 1024), 4)

    def _reserved_ratio(self) -> float:
        r = self._BASE_RESERVED + self._FRAG_RESERVED
        if self.inp.replication:
            r += self._REPL_OVERHEAD
        if "aof" in self.inp.persistence:
            r += self._AOF_OVERHEAD
        return min(r, 0.50)

    def _maxmemory_gb(self) -> float:
        return round(self.inp.ram_gb * (1 - self._reserved_ratio()), 2)

    def _reserved_gb(self) -> float:
        return round(self.inp.ram_gb * self._reserved_ratio(), 2)

    def _eviction(self) -> str:
        return "volatile-lru" if "aof" in self.inp.persistence else "allkeys-lru"

    def _redis_params(self, mm: float, rg: float) -> list[TuningParam]:
        ex = self.inp.existing
        return [
            # MAJOR
            self._param("maxmemory",          f"{mm}gb", M,
                "Hard memory ceiling. Without it Redis grows unbounded and OOMs the OS.",
                f"maxmemory {mm}gb",
                f"{ex.maxmemory_gb}gb" if ex.maxmemory_gb else None),
            self._param("maxmemory-policy",   self._eviction(), M,
                "Controls what Redis evicts when maxmemory is reached. "
                "noeviction causes write errors; allkeys-lru is safe for caches.",
                f"maxmemory-policy {self._eviction()}",
                ex.maxmemory_policy),
            self._param("maxmemory-reserved", f"{rg}gb", M,
                "Reserved headroom for replication, AOF rewrites, client buffers.",
                f"# set maxmemory to leave {rg} GB headroom",
                None),
            # MEDIUM
            self._param("appendonly",
                "yes" if "aof" in self.inp.persistence else "no", MED,
                "AOF persistence survives restarts at cost of ~10% write throughput.",
                f"appendonly {'yes' if 'aof' in self.inp.persistence else 'no'}",
                ex.appendonly),
            self._param("appendfsync",
                "everysec", MED,
                "everysec balances durability and performance. "
                "always is safest but halves write throughput.",
                "appendfsync everysec"),
            self._param("hz",                 "15",    MED,
                "Event loop frequency. 15 (vs default 10) improves expiry precision "
                "under high-key-volume workloads without notable CPU cost.",
                "hz 15",
                str(ex.hz) if ex.hz else None),
            self._param("lazyfree-lazy-eviction", "yes", MED,
                "Eviction runs in background thread, avoiding main-thread latency spikes.",
                "lazyfree-lazy-eviction yes"),
            self._param("tcp-backlog",        "511",   MED,
                "Must not exceed net.core.somaxconn. Default 511 is correct; "
                "verify OS somaxconn is ≥511.",
                "tcp-backlog 511",
                str(ex.tcp_backlog) if ex.tcp_backlog else None),
            # MINOR
            self._param("latency-monitor-threshold", "50", MIN,
                "Log commands slower than 50ms for latency profiling.",
                "latency-monitor-threshold 50"),
            self._param("slowlog-log-slower-than", "10000", MIN,
                "Log commands > 10ms (10000 µs) to slowlog.",
                "slowlog-log-slower-than 10000"),
            self._param("activerehashing",    "yes",   MIN,
                "Incrementally rehash hash tables during idle cycles.",
                "activerehashing yes"),
            self._param("dynamic-hz",         "yes",   MIN,
                "Automatically raises hz under load for better expiry precision.",
                "dynamic-hz yes"),
            self._param("protected-mode",     "yes",   MIN,
                "Blocks unauthenticated access when no bind/requirepass is set.",
                "protected-mode yes"),
        ]

    def _audit(self, mm: float) -> list[str]:
        findings: list[str] = []
        ex = self.inp.existing
        if ex.maxmemory_policy == "noeviction":
            findings.append(
                "maxmemory-policy=noeviction will cause write errors when memory is full. "
                f"Change to {self._eviction()}."
            )
        if ex.maxmemory_gb and ex.maxmemory_gb > mm:
            findings.append(
                f"Existing maxmemory ({ex.maxmemory_gb} GB) exceeds recommended {mm} GB. "
                "Too little headroom for persistence and replication buffers."
            )
        if ex.appendonly == "no" and "aof" in self.inp.persistence:
            findings.append("appendonly=no but AOF persistence requested. Enable appendonly yes.")
        if ex.hz and ex.hz < 10:
            findings.append(f"hz={ex.hz} is very low. Key expiry and background jobs will lag.")
        for k, v in (ex.os_sysctl or {}).items():
            if k == "vm.overcommit_memory" and v != "1":
                findings.append(
                    f"vm.overcommit_memory={v} – MUST be 1 for Redis. "
                    "Fork-based persistence (BGSAVE) will fail with ENOMEM."
                )
            if k == "transparent_hugepage" and v in ("always", "madvise"):
                findings.append(
                    f"transparent_hugepage={v} causes latency spikes during BGSAVE. Set to never."
                )
        return findings

    def _redis_conf(self, mm: float, rg: float) -> str:
        save = ("save 900 1\nsave 300 10\nsave 60 10000"
                if "rdb" in self.inp.persistence else "# RDB save disabled")
        aof_line = ("appendonly yes\nappendfsync everysec"
                    if "aof" in self.inp.persistence else "appendonly no")
        return f"""# ── VAREX redis.conf ({self.inp.mode.value.upper()} mode) ──────────────
bind 127.0.0.1 -::1
protected-mode yes
port 6379

maxmemory {mm}gb
maxmemory-policy {self._eviction()}

{save}
{aof_line}

hz 15
dynamic-hz yes
latency-monitor-threshold 50
slowlog-log-slower-than 10000
activerehashing yes
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
tcp-backlog 511
timeout 300
tcp-keepalive 60
"""

    def _ha_suggestions(self) -> list[str]:
        return [
            "Use Redis Sentinel (≥3 nodes) for automatic failover.",
            "Enable Redis Cluster for horizontal sharding beyond single-node RAM.",
            "Place replicas in separate AZs to survive zone failures.",
            "Set min-replicas-to-write 1 min-replicas-max-lag 10 to prevent split-brain writes.",
            f"With {self.inp.cluster_nodes} nodes run hash-slot rebalance after topology changes."
            if self.inp.cluster_nodes > 1 else
            "Single node detected – add ≥1 replica for HA.",
        ]

    def _perf_warnings(self, ds: float, mm: float) -> list[str]:
        w = []
        if ds > mm:
            w.append(f"Dataset {ds:.2f} GB > maxmemory {mm:.2f} GB – upgrade RAM or enable clustering.")
        if self.inp.persistence == "aof" and self.inp.peak_ops_per_sec > 100_000:
            w.append("AOF + >100K OPS – monitor aof_delayed_fsync; consider appendfsync no under extreme load.")
        if self.inp.cluster_nodes == 1 and self.inp.replication:
            w.append("Replication enabled but cluster_nodes=1 – add replica nodes.")
        return w

    def generate(self) -> RedisOutput:
        ds = self._dataset_gb()
        mm = self._maxmemory_gb()
        rg = self._reserved_gb()
        all_params = self._redis_params(mm, rg)

        os_engine = OSTuningEngine(
            cpu_cores=self.inp.cpu_cores,
            ram_gb=self.inp.ram_gb,
            max_conns=max(10_000, self.inp.peak_ops_per_sec),
            os_type=self.inp.os_type,
            existing_params=dict(self.inp.existing.os_sysctl) if self.inp.existing else {},
            disable_thp=True,
        )
        all_params += os_engine.generate()

        return RedisOutput(
            mode=self.inp.mode,
            estimated_dataset_gb=ds,
            recommended_maxmemory_gb=mm,
            maxmemory_reserved_gb=rg,
            eviction_policy=self._eviction(),
            redis_conf_snippet=self._redis_conf(mm, rg),
            major_params=[p for p in all_params if p.impact == ImpactLevel.MAJOR],
            medium_params=[p for p in all_params if p.impact == ImpactLevel.MEDIUM],
            minor_params=[p for p in all_params if p.impact == ImpactLevel.MINOR],
            os_sysctl_conf=os_engine.sysctl_conf_block(),
            ha_suggestions=self._ha_suggestions(),
            performance_warnings=self._perf_warnings(ds, mm),
            capacity_warning=self._capacity_warning(ds, mm, "Redis maxmemory"),
            audit_findings=self._audit(mm) if self.inp.mode == CalcMode.EXISTING else [],
        )
