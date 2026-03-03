from __future__ import annotations

import math
from typing import Any


SUPPORTED_CALCULATORS = {
    "nginx",
    "redis",
    "tomcat",
    "httpd",
    "ohs",
    "ihs",
    "iis",
    "podman",
    "k8s",
    "os",
    "postgresql",
    "mysql",
    "mongodb",
    "haproxy",
    "docker",
    "rabbitmq",
}


def _to_float(payload: dict[str, Any], key: str, default: float) -> float:
    v = payload.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _to_int(payload: dict[str, Any], key: str, default: int) -> int:
    v = payload.get(key, default)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def example_payload(calculator: str, profile: str) -> dict[str, Any]:
    mode = "existing" if "existing" in profile else "new"
    base = {
        "mode": mode,
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 10000,
        "avg_response_ms": 120,
    }
    per_calc = {
        "redis": {"estimated_keys": 5_000_000},
        "k8s": {"replicas": 3},
        "podman": {"replicas": 2},
        "os": {"workload_type": "web"},
        "iis": {"os_type": "windows-server-2022"},
        "postgresql": {"connections": 300},
        "mysql": {"connections": 300},
        "mongodb": {"connections": 500},
        "haproxy": {"connections": 20000},
        "rabbitmq": {"queues": 200},
    }
    base.update(per_calc.get(calculator, {}))
    return base


def calculate(calculator: str, payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode", "new")).lower()
    cpu = max(1, _to_int(payload, "cpu_cores", 4))
    ram = max(1.0, _to_float(payload, "ram_gb", 8.0))
    rps = max(1, _to_int(payload, "expected_rps", 1000))
    response_ms = max(1, _to_int(payload, "avg_response_ms", 100))

    concurrency = max(1, math.ceil(rps * (response_ms / 1000.0)))
    workers = max(1, cpu)
    max_connections = max(256, workers * max(256, concurrency // workers + 128))
    file_limit = max_connections * 2

    major = [
        {
            "name": "workers",
            "current_value": None,
            "recommended": str(workers),
            "impact": "MAJOR",
            "reason": "Workers scaled to CPU cores to avoid over/under scheduling.",
            "command": f"set workers={workers}",
            "safe_to_apply_live": True,
        },
        {
            "name": "max_connections",
            "current_value": None,
            "recommended": str(max_connections),
            "impact": "MAJOR",
            "reason": "Capacity derived from expected concurrency and response time.",
            "command": f"set max_connections={max_connections}",
            "safe_to_apply_live": False,
        },
    ]
    medium = [
        {
            "name": "open_files_limit",
            "current_value": None,
            "recommended": str(file_limit),
            "impact": "MEDIUM",
            "reason": "File descriptor headroom prevents connection throttling.",
            "command": f"ulimit -n {file_limit}",
            "safe_to_apply_live": True,
        }
    ]
    minor = [
        {
            "name": "keepalive_timeout",
            "current_value": None,
            "recommended": "15",
            "impact": "MINOR",
            "reason": "Balanced keepalive for latency and socket reuse.",
            "command": "set keepalive_timeout=15",
            "safe_to_apply_live": True,
        }
    ]

    calc_specific: dict[str, Any] = {}
    if calculator == "redis":
        keys = max(1, _to_int(payload, "estimated_keys", 1_000_000))
        dataset_gb = max(1.0, keys * 1.5 / (1024 * 1024))
        maxmemory_gb = max(1, int(ram * 0.7))
        calc_specific = {
            "estimated_dataset_gb": round(dataset_gb, 2),
            "recommended_maxmemory_gb": maxmemory_gb,
            "eviction_policy": "allkeys-lru",
        }
    elif calculator in {"postgresql", "mysql", "mongodb"}:
        conns = max(50, _to_int(payload, "connections", 300))
        shared_buffer_mb = int(ram * 1024 * 0.25)
        work_mem_mb = max(4, int((ram * 1024 * 0.4) / max(1, conns)))
        calc_specific = {
            "connections": conns,
            "shared_buffer_mb": shared_buffer_mb,
            "work_mem_mb": work_mem_mb,
        }
    elif calculator in {"k8s", "podman"}:
        replicas = max(1, _to_int(payload, "replicas", 2))
        cpu_request_m = int((cpu / max(1, replicas)) * 1000)
        mem_request_mb = int((ram / max(1, replicas)) * 1024 * 0.7)
        calc_specific = {
            "replicas": replicas,
            "cpu_request_m": cpu_request_m,
            "memory_request_mb": mem_request_mb,
        }

    audit_findings: list[str] = []
    if mode == "existing":
        audit_findings = [
            "Existing mode: compare current parameters against recommended values before apply.",
            "Validate in staging and roll out with canary for production systems.",
        ]

    snippet = (
        f"# {calculator} optimized baseline\n"
        f"workers={workers}\n"
        f"max_connections={max_connections}\n"
        f"open_files_limit={file_limit}\n"
    )

    return {
        "calculator": calculator,
        "mode": mode,
        "workers": workers,
        "estimated_concurrency": concurrency,
        "max_connections": max_connections,
        "config_snippet": snippet,
        "major_params": major,
        "medium_params": medium,
        "minor_params": minor,
        "audit_findings": audit_findings,
        "summary": "Computation completed successfully.",
        **calc_specific,
    }
