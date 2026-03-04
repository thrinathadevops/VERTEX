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
        "nginx": {
            "worker_connections": 4096,
            "client_max_body_size_mb": 10,
            "keepalive_timeout_s": 10,
            "send_timeout_s": 30,
        },
        "redis": {"estimated_keys": 5_000_000},
        "httpd": {
            "limit_request_line_kb": 16,
            "limit_request_field_size_kb": 16,
            "limit_request_body_kb": 1_048_576,
            "keep_alive_timeout_s": 15,
            "max_keep_alive_requests": 500,
            "max_request_workers": 1000,
            "listen_backlog": 2048,
        },
        "ohs": {
            "limit_request_line_kb": 16,
            "limit_request_field_size_kb": 16,
            "limit_request_body_kb": 1_048_576,
            "keep_alive_timeout_s": 15,
            "max_keep_alive_requests": 500,
            "max_client": 1000,
            "max_requests_per_child": 10000,
            "send_buffer_size_kb": 85.33,
            "receive_buffer_size_kb": 85.33,
            "rlimit_mem_kb": 5_242_880,
            "rlimit_cpu_s": 600,
        },
        "ihs": {
            "limit_request_line_kb": 16,
            "limit_request_field_size_kb": 16,
            "limit_request_body_kb": 1_048_576,
            "keep_alive_timeout_s": 15,
            "max_keep_alive_requests": 500,
            "max_request_workers": 1000,
            "max_connections_per_child": 100000,
            "listen_backlog": 2048,
            "send_buffer_size_kb": 85.33,
            "receive_buffer_size_kb": 85.33,
        },
        "k8s": {"replicas": 3},
        "podman": {
            "replicas": 2,
            "cgroup_manager": "systemd",
            "events_backend": "journald",
            "pids_limit": 2048,
            "storage_max_size_gb": 20,
            "storage_driver": "overlay2",
            "log_size_max_mb": 100,
            "default_nofile_soft": 65535,
            "default_nofile_hard": 65535,
        },
        "os": {"workload_type": "web"},
        "iis": {
            "os_type": "windows-server-2022",
            "max_url_length_kb": 2,
            "max_query_string_kb": 1,
            "max_request_headers_kb": 16,
            "max_allowed_content_length_mb": 10,
            "connection_timeout_s": 60,
            "idle_timeout_min": 10,
            "max_concurrent_requests": 5000,
            "allow_double_escaping": False,
            "enable_keep_alive": True,
        },
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
    detailed_params: list[dict[str, Any]] = []

    def add_param(
        name: str,
        current: Any,
        proposed: Any,
        details: str,
        impact: str = "MEDIUM",
    ) -> None:
        detailed_params.append(
            {
                "name": name,
                "current_value": current,
                "recommended": proposed,
                "impact": impact,
                "details": details,
            }
        )

    if calculator == "nginx":
        worker_connections = max(512, _to_int(payload, "worker_connections", 4096))
        client_max_body_size_mb = max(1, _to_int(payload, "client_max_body_size_mb", 10))
        keepalive_timeout_s = max(5, _to_int(payload, "keepalive_timeout_s", 10))
        send_timeout_s = max(5, _to_int(payload, "send_timeout_s", 30))
        add_param("worker_processes", payload.get("worker_processes"), "auto", "Auto scales workers to CPU topology.", "MAJOR")
        add_param("worker_connections", payload.get("worker_connections"), worker_connections, "Concurrent sockets per worker.", "MAJOR")
        add_param("client_max_body_size", payload.get("client_max_body_size_mb"), f"{client_max_body_size_mb}m", "Maximum request body size.")
        add_param("keepalive_timeout", payload.get("keepalive_timeout_s"), f"{keepalive_timeout_s}s", "Idle keepalive timeout.")
        add_param("send_timeout", payload.get("send_timeout_s"), f"{send_timeout_s}s", "Response send timeout.")
        add_param("open_file_cache_max", payload.get("open_file_cache_max"), max(10000, worker_connections * 20), "Cache open files for hot paths.")
        add_param("ssl_protocols", payload.get("ssl_protocols"), "TLSv1.2 TLSv1.3", "Restrict to modern TLS.")
        calc_specific = {"worker_connections": worker_connections}
    if calculator == "redis":
        keys = max(1, _to_int(payload, "estimated_keys", 1_000_000))
        dataset_gb = max(1.0, keys * 1.5 / (1024 * 1024))
        maxmemory_gb = max(1, int(ram * 0.7))
        protected_mode = bool(payload.get("protected_mode", False))
        appendonly = bool(payload.get("appendonly", True))
        eviction_policy = str(payload.get("maxmemory_policy", "allkeys-lru"))
        timeout_s = max(0, _to_int(payload, "timeout_s", 300))
        add_param("maxmemory", payload.get("maxmemory_gb"), f"{maxmemory_gb}gb", "Use ~70% RAM to avoid OOM killer.", "MAJOR")
        add_param("maxmemory_policy", payload.get("maxmemory_policy"), eviction_policy, "Eviction strategy under memory pressure.", "MAJOR")
        add_param("appendonly", payload.get("appendonly"), "yes" if appendonly else "no", "AOF durability for critical data.")
        add_param("protected-mode", payload.get("protected_mode"), "yes" if protected_mode else "no", "Set based on network exposure model.")
        add_param("timeout", payload.get("timeout_s"), timeout_s, "Close idle clients to reclaim resources.")
        calc_specific = {
            "estimated_dataset_gb": round(dataset_gb, 2),
            "recommended_maxmemory_gb": maxmemory_gb,
            "eviction_policy": eviction_policy,
        }
    elif calculator in {"httpd", "ohs", "ihs"}:
        limit_line = max(8, _to_int(payload, "limit_request_line_kb", 16))
        limit_field = max(8, _to_int(payload, "limit_request_field_size_kb", 16))
        limit_body = max(1024, _to_int(payload, "limit_request_body_kb", 1_048_576))
        timeout_s = max(10, _to_int(payload, "timeout_s", 30))
        keepalive_s = max(5, _to_int(payload, "keep_alive_timeout_s", 15))
        max_keepalive = max(100, _to_int(payload, "max_keep_alive_requests", 500))
        add_param("LimitRequestLine", payload.get("limit_request_line_kb"), f"{limit_line}KB", "Maximum HTTP request line.")
        add_param("LimitRequestFieldSize", payload.get("limit_request_field_size_kb"), f"{limit_field}KB", "Maximum header field size.")
        add_param("LimitRequestBody", payload.get("limit_request_body_kb"), f"{limit_body}KB", "Maximum request body size.")
        add_param("Timeout", payload.get("timeout_s"), f"{timeout_s}s", "I/O timeout between client and server.")
        add_param("KeepAliveTimeout", payload.get("keep_alive_timeout_s"), f"{keepalive_s}s", "Persistent connection wait time.")
        add_param("MaxKeepAliveRequests", payload.get("max_keep_alive_requests"), max_keepalive, "Requests per persistent connection.", "MAJOR")
        if calculator == "ihs":
            mrw = max(150, _to_int(payload, "max_request_workers", 1000))
            add_param("MaxRequestWorker", payload.get("max_request_workers"), mrw, "Simultaneous client connections.", "MAJOR")
        if calculator == "ohs":
            mc = max(150, _to_int(payload, "max_client", 1000))
            mrpc = max(1000, _to_int(payload, "max_requests_per_child", 10000))
            add_param("MaxClient", payload.get("max_client"), mc, "Simultaneous clients served.", "MAJOR")
            add_param("MaxRequestPerChild", payload.get("max_requests_per_child"), mrpc, "Requests per child before recycle.")
        calc_specific = {"request_guard_profile": "strict"}
    elif calculator == "iis":
        max_url = max(1, _to_int(payload, "max_url_length_kb", 2))
        max_qs = max(1, _to_int(payload, "max_query_string_kb", 1))
        max_hdr = max(4, _to_int(payload, "max_request_headers_kb", 16))
        max_body = max(1, _to_int(payload, "max_allowed_content_length_mb", 10))
        conn_to = max(10, _to_int(payload, "connection_timeout_s", 60))
        idle_to = max(1, _to_int(payload, "idle_timeout_min", 10))
        max_req = max(500, _to_int(payload, "max_concurrent_requests", 5000))
        add_param("maxUrl", payload.get("max_url_length_kb"), f"{max_url}KB", "Maximum URL size.")
        add_param("maxQueryString", payload.get("max_query_string_kb"), f"{max_qs}KB", "Maximum query string size.")
        add_param("maxRequestHeadersTotalSize", payload.get("max_request_headers_kb"), f"{max_hdr}KB", "Maximum aggregate header size.")
        add_param("maxAllowedContentLength", payload.get("max_allowed_content_length_mb"), f"{max_body}MB", "Maximum upload/request size.")
        add_param("connectionTimeout", payload.get("connection_timeout_s"), f"{conn_to}s", "Idle connection timeout.")
        add_param("idleTimeout", payload.get("idle_timeout_min"), f"{idle_to}min", "Application idle timeout.")
        add_param("maxConcurrentRequestsPerCPU", payload.get("max_concurrent_requests"), max_req, "Maximum simultaneous requests.", "MAJOR")
        add_param("allowDoubleEscaping", payload.get("allow_double_escaping"), bool(payload.get("allow_double_escaping", False)), "Keep disabled unless legacy app requires it.")
        add_param("keepAlive", payload.get("enable_keep_alive"), bool(payload.get("enable_keep_alive", True)), "Connection reuse for performance.")
        calc_specific = {"request_filtering_profile": "hardened"}
    elif calculator in {"postgresql", "mysql", "mongodb"}:
        conns = max(50, _to_int(payload, "connections", 300))
        shared_buffer_mb = int(ram * 1024 * 0.25)
        work_mem_mb = max(4, int((ram * 1024 * 0.4) / max(1, conns)))
        calc_specific = {
            "connections": conns,
            "shared_buffer_mb": shared_buffer_mb,
            "work_mem_mb": work_mem_mb,
        }
        add_param("connections", payload.get("connections"), conns, "Connection pool cap.", "MAJOR")
        add_param("shared_buffers", payload.get("shared_buffer_mb"), f"{shared_buffer_mb}MB", "DB shared memory.")
        add_param("work_mem", payload.get("work_mem_mb"), f"{work_mem_mb}MB", "Per operation memory.")
    elif calculator in {"k8s", "podman"}:
        replicas = max(1, _to_int(payload, "replicas", 2))
        cpu_request_m = int((cpu / max(1, replicas)) * 1000)
        mem_request_mb = int((ram / max(1, replicas)) * 1024 * 0.7)
        calc_specific = {
            "replicas": replicas,
            "cpu_request_m": cpu_request_m,
            "memory_request_mb": mem_request_mb,
        }
        add_param("replicas", payload.get("replicas"), replicas, "Baseline horizontal scale factor.", "MAJOR")
        add_param("cpu_request", payload.get("cpu_request_m"), f"{cpu_request_m}m", "CPU request per replica.")
        add_param("memory_request", payload.get("memory_request_mb"), f"{mem_request_mb}Mi", "Memory request per replica.")
        if calculator == "podman":
            add_param("cgroup_manager", payload.get("cgroup_manager"), str(payload.get("cgroup_manager", "systemd")), "Stable resource control integration.")
            add_param("events_backend", payload.get("events_backend"), str(payload.get("events_backend", "journald")), "Centralized audit logging.")
            add_param("pids_limit", payload.get("pids_limit"), max(512, _to_int(payload, "pids_limit", 2048)), "Fork-bomb guardrail.")
            add_param("log_size_max", payload.get("log_size_max_mb"), f"{max(10, _to_int(payload, 'log_size_max_mb', 100))}m", "Limit log growth.")
            add_param("default_ulimits_nofile", payload.get("default_nofile_soft"), f"{_to_int(payload, 'default_nofile_soft', 65535)}:{_to_int(payload, 'default_nofile_hard', 65535)}", "Increase file descriptors.")

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
        "recommended_params": detailed_params,
        "audit_findings": audit_findings,
        "summary": "Computation completed successfully.",
        **calc_specific,
    }
