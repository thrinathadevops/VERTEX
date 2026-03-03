"""
app/api/v1/redis.py
===================
FastAPI router for the Redis tuning calculator.

Endpoints
---------
POST /api/v1/redis/calculate
    mode=new      → generate fresh redis.conf from hardware + workload specs
    mode=existing → audit current redis.conf and return safe upgrade plan

POST /api/v1/redis/example/new
    Returns a pre-filled example NEW mode request body

POST /api/v1/redis/example/existing
    Returns a pre-filled EXISTING mode audit body with common misconfigs
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.redis import RedisInput, RedisOutput
from app.calculators.redis_calculator import RedisCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=RedisOutput,
    summary="Redis – Calculate optimal config (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide hardware specs + workload profile, receive:
- Calculated `maxmemory` with full reservation formula breakdown
- `maxmemory-policy` selected based on your persistence mode
- Complete `redis.conf` snippet ready to deploy
- 20+ tiered params (MAJOR/MEDIUM/MINOR) with formula-backed explanations
- OS sysctl block (including vm.overcommit_memory and THP disable — mandatory for Redis)

**EXISTING mode** — additionally supply current `redis.conf` values in the `existing` block:
- `audit_findings`: MAJOR/MEDIUM issues (unauthenticated Redis, noeviction, wrong THP, etc.)
- `current_value` on every param: what you have vs what VAREX recommends
- Safe upgrade path with `safe_to_apply_live` flags

**Critical OS params** automatically included:
- `vm.overcommit_memory=1` (BGSAVE fork ENOMEM prevention)
- `transparent_hugepage=never` (BGSAVE latency spike prevention)
- `vm.swappiness=1` for Redis-only nodes
    """,
)
def calculate_redis(inp: RedisInput) -> RedisOutput:
    """
    Calculate optimal Redis configuration.

    Raises 422 for invalid input combinations (e.g. negative RAM, zero keys).
    Raises 500 for unexpected calculation errors.
    """
    try:
        result = RedisCalculator(inp).generate()
        logger.info(
            "Redis calculate",
            extra={
                "mode":          inp.mode.value,
                "ram_gb":        inp.ram_gb,
                "maxmemory_gb":  result.recommended_maxmemory_gb,
                "reserved_gb":   result.maxmemory_reserved_gb,
                "dataset_gb":    result.estimated_dataset_gb,
                "eviction":      result.eviction_policy,
                "persistence":   inp.persistence,
                "audit_count":   len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("Redis validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new",
    summary="Redis – Example NEW mode request",
    include_in_schema=True,
)
def redis_example_new() -> JSONResponse:
    """Returns a sample NEW mode request body — copy-paste into /calculate."""
    return JSONResponse({
        "mode":             "new",
        "cpu_cores":        4,
        "ram_gb":           32,
        "os_type":          "ubuntu-22",
        "avg_key_size_kb":  2.0,
        "estimated_keys":   5_000_000,
        "persistence":      "rdb+aof",
        "replication":      True,
        "cluster_nodes":    3,
        "peak_ops_per_sec": 50_000,
    })


@router.post(
    "/example/existing",
    summary="Redis – Example EXISTING mode audit (with common misconfigs)",
    include_in_schema=True,
)
def redis_example_existing() -> JSONResponse:
    """
    Returns a sample EXISTING mode body with intentional misconfigurations:
    - noeviction policy (will OOM-error on write when full)
    - requirepass NOT set (unauthenticated)
    - bind=0.0.0.0 (exposed on all interfaces)
    - appendonly=no (persistence silently disabled)
    - vm.overcommit_memory=0 (BGSAVE fork failures)
    - transparent_hugepage=always (2–10s latency spikes)
    """
    return JSONResponse({
        "mode":             "existing",
        "cpu_cores":        4,
        "ram_gb":           32,
        "os_type":          "rhel-8",
        "avg_key_size_kb":  2.0,
        "estimated_keys":   5_000_000,
        "persistence":      "aof",
        "replication":      True,
        "cluster_nodes":    1,
        "peak_ops_per_sec": 50_000,
        "existing": {
            "maxmemory_gb":     28.0,
            "maxmemory_policy": "noeviction",
            "appendonly":       "no",
            "hz":               10,
            "requirepass_set":  False,
            "bind":             "0.0.0.0",
            "protected_mode":   "no",
            "timeout":          0,
            "redis_version":    "7.0.11",
            "maxclients":       10000,
            "os_sysctl": {
                "vm.overcommit_memory":    "0",
                "transparent_hugepage":    "always",
                "net.core.somaxconn":      "128",
                "vm.swappiness":           "60",
                "fs.file-max":             "65536",
            },
        },
    })
