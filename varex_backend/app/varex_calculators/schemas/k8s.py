"""
app/schemas/k8s.py
==================
Pydantic schemas for the Kubernetes workload tuning calculator.

Kubernetes resource model:
  requests  — guaranteed allocation (scheduler uses this for bin-packing)
  limits    — hard cap (CPU: throttled; Memory: OOM killed)
  QoS classes:
    Guaranteed  → requests == limits for ALL containers
    Burstable   → requests < limits
    BestEffort  → no requests/limits set (evicted first)

Three models:
  K8sExisting  — current Pod spec resource fields for EXISTING mode audit
  K8sInput     — request body (NEW and EXISTING modes)
  K8sOutput    — full calculator response
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from app.varex_calculators.core.enums import OSType, CalcMode
from app.varex_calculators.core.models import TuningParam


# ── existing config (EXISTING mode only) ─────────────────────────────────
class K8sExisting(BaseModel):
    """Current Pod spec resource values. All optional."""
    cpu_request_m:           int   | None = None   # millicores e.g. 250
    cpu_limit_m:             int   | None = None   # millicores e.g. 500
    memory_request_mb:       int   | None = None   # MiB
    memory_limit_mb:         int   | None = None   # MiB
    liveness_probe:          bool  | None = None
    readiness_probe:         bool  | None = None
    hpa_enabled:             bool  | None = None
    hpa_min_replicas:        int   | None = None
    hpa_max_replicas:        int   | None = None
    hpa_cpu_target:          int   | None = None   # percent
    pdb_enabled:             bool  | None = None
    replicas:                int   | None = None
    qos_class:               str   | None = None   # Guaranteed/Burstable/BestEffort
    node_selector:           dict[str, str] = {}
    topology_spread:         bool  | None = None
    pod_disruption_budget:   bool  | None = None
    image_pull_policy:       str   | None = None


# ── request input ─────────────────────────────────────────────────────────
class K8sInput(BaseModel):
    """
    Workload + cluster parameters for Kubernetes tuning.

    mode
        new      → generate Pod spec + HPA + PDB + NetworkPolicy YAML
        existing → audit K8sExisting and return safe upgrade plan

    node_cpu_cores        : vCPU per node (for requests/limits ratio check)
    node_ram_gb           : RAM per node (GB)
    os_type               : node OS
    container_cpu_cores   : CPU cores to REQUEST for one container replica
    container_ram_gb      : RAM to REQUEST for one container replica (GB)
    workload_type         : drives QoS + HPA + probe recommendations
                            web       → Burstable QoS, HPA on CPU, readiness critical
                            worker    → Burstable, HPA on custom metric / KEDA
                            database  → Guaranteed QoS, StatefulSet, no HPA
                            cache     → Guaranteed QoS, no HPA
                            batch     → BestEffort acceptable, Job/CronJob
    replicas              : desired replica count
    target_rps            : requests per second per replica (for HPA sizing)
    avg_request_ms        : average request ms (for timeout/probe tuning)
    qos_class             : Guaranteed / Burstable / BestEffort
                            auto → calculator chooses based on workload_type
    enable_hpa            : generate HPA manifest
    enable_pdb            : generate PodDisruptionBudget manifest
    enable_network_policy : generate deny-all + allow-ingress NetworkPolicy
    namespace             : Kubernetes namespace
    service_account       : ServiceAccount name (for RBAC)
    node_pool_label       : node selector label key=value
    """
    mode:                  CalcMode = CalcMode.NEW

    node_cpu_cores:        Annotated[int,   Field(ge=1,   le=1024)]
    node_ram_gb:           Annotated[float, Field(gt=0,   le=4096)]
    os_type:               OSType   = OSType.RHEL_9
    container_cpu_cores:   Annotated[float, Field(gt=0,   le=512,  default=1.0)]
    container_ram_gb:      Annotated[float, Field(gt=0,   le=4096, default=2.0)]
    workload_type:         Literal["web", "worker", "database", "cache", "batch"] = "web"
    replicas:              Annotated[int,   Field(ge=1,   le=1000, default=3)]
    target_rps:            Annotated[int,   Field(ge=1,             default=100)]
    avg_request_ms:        Annotated[int,   Field(ge=1,   le=300_000, default=200)]
    qos_class:             Literal["Guaranteed", "Burstable", "BestEffort", "auto"] = "auto"
    enable_hpa:            bool = True
    enable_pdb:            bool = True
    enable_network_policy: bool = True
    namespace:             str  = "default"
    service_account:       str  = "default"
    node_pool_label:       str  = "app=varex"
    existing:              K8sExisting = Field(default_factory=K8sExisting)

    model_config = {
        "json_schema_extra": {
            "examples": {
                "new_web": {
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
                },
                "new_database": {
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
                },
                "existing_audit": {
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
                },
            }
        }
    }


# ── response output ───────────────────────────────────────────────────────
class K8sOutput(BaseModel):
    """Full Kubernetes calculator response."""
    mode:                       CalcMode

    # ── calculated values ──
    cpu_request_m:              int    # millicores
    cpu_limit_m:                int    # millicores
    memory_request_mb:          int    # MiB
    memory_limit_mb:            int    # MiB
    effective_qos_class:        str
    recommended_replicas:       int
    hpa_min_replicas:           int
    hpa_max_replicas:           int
    hpa_cpu_target_percent:     int

    # ── ready-to-use YAML ──
    deployment_yaml:            str    # Deployment / StatefulSet manifest
    hpa_yaml:                   str    # HorizontalPodAutoscaler manifest
    pdb_yaml:                   str    # PodDisruptionBudget manifest
    network_policy_yaml:        str    # NetworkPolicy manifests

    # ── tiered params ──
    major_params:               list[TuningParam]
    medium_params:              list[TuningParam]
    minor_params:               list[TuningParam]

    # ── node tuning ──
    os_sysctl_conf:             str    # node-level sysctl (DaemonSet or node config)

    # ── advisory outputs ──
    ha_suggestions:             list[str]
    performance_warnings:       list[str]
    capacity_warning:           str | None

    # ── EXISTING mode only ──
    audit_findings:             list[str] = []


