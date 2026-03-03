"""
app/api/v1/k8s.py
=================
FastAPI router for the Kubernetes workload tuning calculator.

Endpoints
---------
POST /api/v1/k8s/calculate
    mode=new      → generate Deployment/StatefulSet + HPA + PDB + NetworkPolicy YAML
    mode=existing → audit current Pod spec and return upgrade plan

POST /api/v1/k8s/example/new-web
    Pre-filled NEW mode — web Deployment (Burstable QoS, HPA, PDB)

POST /api/v1/k8s/example/new-database
    Pre-filled NEW mode — database StatefulSet (Guaranteed QoS, PDB only)

POST /api/v1/k8s/example/existing
    Pre-filled EXISTING audit — BestEffort QoS, no probes, no HPA, replicas=1
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.k8s import K8sInput, K8sOutput
from app.calculators.k8s_calculator import K8sCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=K8sOutput,
    summary="K8s – Calculate Pod resources + HPA + PDB + NetworkPolicy (NEW & EXISTING modes)",
    description="""
**NEW mode** — provide node + container specs, receive:
- `cpu.requests` = `container_cpu_cores × 1000` millicores
- `cpu.limits` = `requests` (Guaranteed) or `requests × 2` (Burstable)
- `memory.requests` = `container_ram_gb × 1024` MiB
- `memory.limits` = `requests` (Guaranteed/database) or `requests × 1.5` (Burstable)
- QoS class auto-selection: database/cache → Guaranteed, web/worker → Burstable, batch → BestEffort
- Complete `Deployment` / `StatefulSet` YAML with probes, security context, anti-affinity
- `HorizontalPodAutoscaler` YAML (min/max replicas, CPU + memory metrics, scale behavior)
- `PodDisruptionBudget` YAML (minAvailable = ceil(replicas × 50%))
- 3× `NetworkPolicy` YAMLs (deny-all, allow-ingress, allow-DNS)
- Node-level sysctl block

**EXISTING mode** — audit your current Pod spec:
- BestEffort QoS (no requests/limits set)
- Missing liveness / readiness probes
- `replicas=1` (single point of failure)
- No HPA for web/worker workloads
- No PodDisruptionBudget (node drain kills all pods)
- No topologySpreadConstraints (all pods co-located on same node)
- `imagePullPolicy=Always` (registry outage = pod start failure)

**Workload-type-specific:**
- `database`: Guaranteed QoS, StatefulSet, no HPA, `memory-swap=memory` (no swap)
- `web`: Burstable, Deployment, HPA (CPU 60%), readiness critical
- `batch`: BestEffort acceptable, Job/CronJob recommended
    """,
)
def calculate_k8s(inp: K8sInput) -> K8sOutput:
    try:
        result = K8sCalculator(inp).generate()
        logger.info(
            "K8s calculate",
            extra={
                "mode":             inp.mode.value,
                "workload_type":    inp.workload_type,
                "replicas":         inp.replicas,
                "cpu_req_m":        result.cpu_request_m,
                "mem_req_mb":       result.memory_request_mb,
                "qos":              result.effective_qos_class,
                "hpa_max":          result.hpa_max_replicas,
                "audit_count":      len(result.audit_findings),
            },
        )
        return result
    except ValueError as e:
        logger.warning("K8s validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/example/new-web",
    summary="K8s – Example NEW mode (web Deployment, Burstable QoS, HPA)",
    include_in_schema=True,
)
def k8s_example_new_web() -> JSONResponse:
    return JSONResponse({
        "mode":                  "new",
        "node_cpu_cores":         8,
        "node_ram_gb":            32,
        "os_type":                "rhel-9",
        "container_cpu_cores":    1.0,
        "container_ram_gb":       2.0,
        "workload_type":          "web",
        "replicas":               3,
        "target_rps":             100,
        "avg_request_ms":         200,
        "qos_class":              "auto",
        "enable_hpa":             True,
        "enable_pdb":             True,
        "enable_network_policy":  True,
        "namespace":              "production",
        "service_account":        "web-sa",
        "node_pool_label":        "app=varex",
    })


@router.post(
    "/example/new-database",
    summary="K8s – Example NEW mode (database StatefulSet, Guaranteed QoS, PDB only)",
    include_in_schema=True,
)
def k8s_example_new_database() -> JSONResponse:
    """
    Database-specific:
    - qos_class=Guaranteed: requests == limits — no CPU throttling, no memory burst
    - enable_hpa=False: StatefulSets should NOT use CPU-based HPA
    - replicas=3: 3-node cluster (primary + 2 replicas)
    - PDB minAvailable=2: 1 node can be drained at a time
    """
    return JSONResponse({
        "mode":                  "new",
        "node_cpu_cores":         8,
        "node_ram_gb":            32,
        "os_type":                "rhel-9",
        "container_cpu_cores":    2.0,
        "container_ram_gb":       8.0,
        "workload_type":          "database",
        "replicas":               3,
        "target_rps":             500,
        "avg_request_ms":         50,
        "qos_class":              "Guaranteed",
        "enable_hpa":             False,
        "enable_pdb":             True,
        "enable_network_policy":  True,
        "namespace":              "data",
        "service_account":        "db-sa",
        "node_pool_label":        "tier=database",
    })


@router.post(
    "/example/existing",
    summary="K8s – Example EXISTING mode audit (BestEffort, no probes, no HPA, replicas=1)",
    include_in_schema=True,
)
def k8s_example_existing() -> JSONResponse:
    """
    Common Kubernetes anti-patterns:
    - No cpu/memory requests or limits → BestEffort QoS → evicted first
    - replicas=1 → single point of failure
    - No liveness/readiness probes → deadlocked container stays Running
    - No HPA → can't handle traffic bursts
    - No PDB → node drain kills all pods
    - No topologySpread → all pods on same node
    - imagePullPolicy=Always → registry outage = startup failure
    """
    return JSONResponse({
        "mode":                  "existing",
        "node_cpu_cores":         8,
        "node_ram_gb":            32,
        "os_type":                "rhel-9",
        "container_cpu_cores":    1.0,
        "container_ram_gb":       2.0,
        "workload_type":          "web",
        "replicas":               1,
        "target_rps":             100,
        "avg_request_ms":         200,
        "qos_class":              "BestEffort",
        "enable_hpa":             False,
        "enable_pdb":             False,
        "enable_network_policy":  False,
        "namespace":              "default",
        "service_account":        "default",
        "node_pool_label":        "app=varex",
        "existing": {
            "cpu_request_m":       None,
            "cpu_limit_m":         None,
            "memory_request_mb":   None,
            "memory_limit_mb":     None,
            "liveness_probe":      False,
            "readiness_probe":     False,
            "hpa_enabled":         False,
            "pdb_enabled":         False,
            "replicas":            1,
            "qos_class":           "BestEffort",
            "topology_spread":     False,
            "image_pull_policy":   "Always",
        },
    })
