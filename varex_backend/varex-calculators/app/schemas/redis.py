"""
app/schemas/redis.py
====================
Pydantic schemas for the Redis tuning calculator.

Three models:
  RedisExisting  — current redis.conf values for EXISTING mode audit
  RedisInput     — request body (NEW and EXISTING modes)
  RedisOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class RedisExisting(BaseModel):
    """
    Supply your current redis.conf values.
    All fields are optional — only supplied fields are audited.

    os_sysctl: current kernel values for OS-level audit, e.g.
               {"vm.overcommit_memory": "0", "transparent_hugepage": "always"}
    """
    maxmemory_gb:     float | None = None   # current maxmemory in GB
    maxmemory_policy: str   | None = None   # e.g. "noeviction", "allkeys-lru"
    appendonly:       str   | None = None   # "yes" or "no"
    hz:               int   | None = None   # e.g. 10
    tcp_backlog:      int   | None = None   # e.g. 511
    requirepass_set:  bool          = False  # True if requirepass is configured
    bind:             str   | None = None   # e.g. "0.0.0.0" or "127.0.0.1"
    protected_mode:   str   | None = None   # "yes" or "no"
    timeout:          int   | None = None   # idle client timeout seconds
    redis_version:    str   | None = None   # e.g. "7.2.4"
    save_enabled:     bool          = True   # whether RDB save is configured
    maxclients:       int   | None = None   # current maxclients setting
    os_sysctl:        dict[str, str] = {}


# ── request input ─────────────────────────────────────────────────────────
class RedisInput(BaseModel):
    """
    Hardware + workload parameters for Redis tuning.

    mode
        new      → generate fresh redis.conf from hardware + workload specs
        existing → audit RedisExisting values and return safe upgrade plan

    cpu_cores          : vCPU count (Redis is single-threaded per shard,
                         but OS + background threads use remaining cores)
    ram_gb             : total RAM on the host (GB)
    os_type            : host OS — drives OS sysctl recommendations
    avg_key_size_kb    : average size of a single key+value pair (KB)
    estimated_keys     : total number of keys in the dataset
    persistence        : durability mode
                         none    → pure cache, no disk writes
                         rdb     → periodic RDB snapshots
                         aof     → append-only file (everysec)
                         rdb+aof → both (AOF used on restart, RDB for backup)
    replication        : True if this node is a primary with replicas
                         (adds 10% COW reservation to maxmemory headroom)
    cluster_nodes      : number of Redis Cluster nodes (used for HA advice)
    peak_ops_per_sec   : expected peak OPS (used for OS max_conns sizing)
    """
    mode:             CalcMode = CalcMode.NEW

    cpu_cores:        Annotated[int,   Field(ge=1,    le=512)]
    ram_gb:           Annotated[float, Field(gt=0,    le=4096)]
    os_type:          OSType    = OSType.UBUNTU_22
    avg_key_size_kb:  Annotated[float, Field(gt=0,    le=102400)]
    estimated_keys:   Annotated[int,   Field(ge=1)]
    persistence:      Literal["none", "rdb", "aof", "rdb+aof"] = "rdb"
    replication:      bool  = False
    cluster_nodes:    Annotated[int,   Field(ge=1,    le=1000,  default=1)]
    peak_ops_per_sec: Annotated[int,   Field(ge=1,              default=10000)]
    existing:         RedisExisting = Field(default_factory=RedisExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_cache": {
                    "mode": "new",
                    "cpu_cores": 4,
                    "ram_gb": 32,
                    "os_type": "ubuntu-22",
                    "avg_key_size_kb": 2.0,
                    "estimated_keys": 5000000,
                    "persistence": "rdb+aof",
                    "replication": True,
                    "cluster_nodes": 3,
                    "peak_ops_per_sec": 50000,
                },
                "existing_audit": {
                    "mode": "existing",
                    "cpu_cores": 4,
                    "ram_gb": 32,
                    "os_type": "rhel-8",
                    "avg_key_size_kb": 2.0,
                    "estimated_keys": 5000000,
                    "persistence": "aof",
                    "replication": True,
                    "cluster_nodes": 1,
                    "peak_ops_per_sec": 50000,
                    "existing": {
                        "maxmemory_gb": 28,
                        "maxmemory_policy": "noeviction",
                        "appendonly": "no",
                        "hz": 10,
                        "requirepass_set": False,
                        "bind": "0.0.0.0",
                        "protected_mode": "no",
                        "timeout": 0,
                        "redis_version": "7.0.11",
                        "os_sysctl": {
                            "vm.overcommit_memory": "0",
                            "transparent_hugepage": "always",
                            "net.core.somaxconn": "128",
                        },
                    },
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class RedisOutput(BaseModel):
    """Full Redis calculator response."""
    mode:                      CalcMode

    # ── calculated values ──
    estimated_dataset_gb:      float    # avg_key_size_kb × estimated_keys
    recommended_maxmemory_gb:  float    # RAM × (1 - reserved_ratio)
    maxmemory_reserved_gb:     float    # RAM × reserved_ratio (OS + frag + COW)
    reserved_ratio_breakdown:  str      # human-readable breakdown of reservation
    eviction_policy:           str      # recommended maxmemory-policy

    # ── ready-to-use config ──
    redis_conf_snippet:        str

    # ── tiered params ──
    major_params:              list[TuningParam]
    medium_params:             list[TuningParam]
    minor_params:              list[TuningParam]

    # ── OS tuning ──
    os_sysctl_conf:            str

    # ── advisory outputs ──
    ha_suggestions:            list[str]
    performance_warnings:      list[str]
    capacity_warning:          str | None

    # ── EXISTING mode only ──
    audit_findings:            list[str] = []
