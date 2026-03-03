"""
app/calculators/k8s_calculator.py
===================================
Kubernetes workload tuning calculator — NEW and EXISTING modes.

Resource formula
----------------
cpu_request_m  = int(container_cpu_cores × 1000)   millicores
cpu_limit_m:
  Guaranteed  → = cpu_request_m
  Burstable   → cpu_request_m × 2   (burst up to 2× on idle nodes)
  BestEffort  → no limit

memory_request_mb = int(container_ram_gb × 1024)
memory_limit_mb:
  Guaranteed  → = memory_request_mb
  Burstable   → memory_request_mb × 1.5
  database    → = memory_request_mb (no burst — OOM kills DB)

QoS auto-selection:
  database / cache → Guaranteed  (evicted last, no throttling)
  web / worker     → Burstable   (burst on spare capacity)
  batch            → BestEffort  (non-critical, evicted first)

HPA sizing:
  hpa_min  = replicas
  hpa_max  = replicas × 4   (capped at node_capacity floor)
  cpu_target = 60% for web/worker, 80% for batch

PDB:
  minAvailable = max(1, ceil(replicas × 0.5))
  Ensures at least 50% of pods survive a voluntary disruption (node drain).

Probes (period/timeout based on avg_request_ms):
  liveness  initialDelaySeconds = 30s, periodSeconds = 10s, timeoutSeconds = 5s
  readiness periodSeconds = 5s, failureThreshold = 3
  startup   failureThreshold = 30 (allows 5min for slow-start apps)
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.k8s import K8sInput, K8sOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


def _mc(cores: float) -> int:
    """Convert CPU cores to millicores."""
    return int(cores * 1000)


class K8sCalculator(BaseCalculator):

    def __init__(self, inp: K8sInput) -> None:
        self._require_positive(inp.node_cpu_cores,      "node_cpu_cores")
        self._require_positive(inp.node_ram_gb,         "node_ram_gb")
        self._require_positive(inp.container_cpu_cores, "container_cpu_cores")
        self._require_positive(inp.container_ram_gb,    "container_ram_gb")
        self.inp = inp

    # ── QoS resolution ────────────────────────────────────────────────────────

    def _qos(self) -> str:
        if self.inp.qos_class != "auto":
            return self.inp.qos_class
        return {
            "database": "Guaranteed",
            "cache":    "Guaranteed",
            "web":      "Burstable",
            "worker":   "Burstable",
            "batch":    "BestEffort",
        }.get(self.inp.workload_type, "Burstable")

    # ── resource calculations ─────────────────────────────────────────────────

    def _cpu_req(self) -> int:
        return _mc(self.inp.container_cpu_cores)

    def _cpu_lim(self) -> int:
        qos = self._qos()
        req = self._cpu_req()
        if qos == "Guaranteed":
            return req
        if qos == "BestEffort":
            return 0   # no limit for BestEffort
        # Burstable
        if self.inp.workload_type == "database":
            return req
        return req * 2

    def _mem_req(self) -> int:
        return int(self.inp.container_ram_gb * 1024)

    def _mem_lim(self) -> int:
        qos = self.inp.qos_class if self.inp.qos_class != "auto" else self._qos()
        req = self._mem_req()
        if qos == "Guaranteed":
            return req
        if qos == "BestEffort":
            return 0
        # Burstable
        if self.inp.workload_type in ("database", "cache"):
            return req   # no burst for stateful
        return int(req * 1.5)

    def _hpa_min(self) -> int:
        return max(2, self.inp.replicas)

    def _hpa_max(self) -> int:
        node_cap = math.floor(self.inp.node_ram_gb / self.inp.container_ram_gb)
        return min(self.inp.replicas * 4, max(self.inp.replicas * 2, node_cap))

    def _hpa_cpu_target(self) -> int:
        return {"batch": 80, "worker": 70}.get(self.inp.workload_type, 60)

    def _pdb_min_available(self) -> int:
        return max(1, math.ceil(self.inp.replicas * 0.5))

    def _probe_timeout(self) -> int:
        return max(5, math.ceil(self.inp.avg_request_ms / 1000) + 2)

    # ── YAML renderers ────────────────────────────────────────────────────────

    def _render_deployment(self) -> str:
        inp       = self.inp
        qos       = self._qos()
        req_cpu   = self._cpu_req()
        lim_cpu   = self._cpu_lim()
        req_mem   = self._mem_req()
        lim_mem   = self._mem_lim()
        pt        = self._probe_timeout()
        kind      = "StatefulSet" if inp.workload_type in ("database", "cache") else "Deployment"

        cpu_req_str = f"{req_cpu}m"
        cpu_lim_str = f"{lim_cpu}m" if lim_cpu else "# no limit (BestEffort)"
        mem_req_str = f"{req_mem}Mi"
        mem_lim_str = f"{lim_mem}Mi" if lim_mem else "# no limit (BestEffort)"

        topology_block = (
            "  topologySpreadConstraints:
"
            "  - maxSkew: 1
"
            "    topologyKey: kubernetes.io/hostname
"
            "    whenUnsatisfiable: DoNotSchedule
"
            f"    labelSelector:
"
            f"      matchLabels:
"
            f"        app: varex-{inp.workload_type}
"
        ) if inp.workload_type not in ("database", "cache") else ""

        affinity_block = (
            "  affinity:
"
            "    podAntiAffinity:
"
            "      preferredDuringSchedulingIgnoredDuringExecution:
"
            "      - weight: 100
"
            "        podAffinityTerm:
"
            "          topologyKey: kubernetes.io/hostname
"
            "          labelSelector:
"
            "            matchLabels:
"
            f"              app: varex-{inp.workload_type}
"
        )

        probe_block = (
            "        livenessProbe:
"
            "          httpGet:
"
            "            path: /healthz
"
            "            port: 8080
"
            "          initialDelaySeconds: 30
"
            "          periodSeconds: 10
"
            f"          timeoutSeconds: {pt}
"
            "          failureThreshold: 3
"
            "        readinessProbe:
"
            "          httpGet:
"
            "            path: /ready
"
            "            port: 8080
"
            "          initialDelaySeconds: 5
"
            "          periodSeconds: 5
"
            f"          timeoutSeconds: {pt}
"
            "          failureThreshold: 3
"
            "        startupProbe:
"
            "          httpGet:
"
            "            path: /healthz
"
            "            port: 8080
"
            "          failureThreshold: 30
"
            "          periodSeconds: 10
"
        ) if inp.workload_type != "batch" else ""

        resources_block = (
            "        resources:
"
            "          requests:
"
            f"            cpu: {cpu_req_str}
"
            f"            memory: {mem_req_str}
"
        )
        if lim_cpu or lim_mem:
            resources_block += (
                "          limits:
"
                + (f"            cpu: {cpu_lim_str}
" if lim_cpu else "") +
                + (f"            memory: {mem_lim_str}
" if lim_mem else "")
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗
"
            f"# ║  VAREX Kubernetes  [{inp.mode.value.upper():8s}]  "
            f"type={inp.workload_type}  QoS={qos}  ║
"
            f"# ╚══════════════════════════════════════════════════════════════╝
"
            f"apiVersion: apps/v1
"
            f"kind: {kind}
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}
"
            f"  namespace: {inp.namespace}
"
            f"  labels:
"
            f"    app: varex-{inp.workload_type}
"
            f"    varex.io/qos: {qos}
"
            f"spec:
"
            f"  replicas: {inp.replicas}
"
            f"  selector:
"
            f"    matchLabels:
"
            f"      app: varex-{inp.workload_type}
"
            f"  template:
"
            f"    metadata:
"
            f"      labels:
"
            f"        app: varex-{inp.workload_type}
"
            f"    spec:
"
            f"      serviceAccountName: {inp.service_account}
"
            f"      automountServiceAccountToken: false
"
            f"      nodeSelector:
"
            f"        {inp.node_pool_label.split('=')[0]}: "
            f"{inp.node_pool_label.split('=')[1] if '=' in inp.node_pool_label else inp.node_pool_label}
"
            f"{affinity_block}"
            f"{topology_block}"
            f"      terminationGracePeriodSeconds: 60
"
            f"      securityContext:
"
            f"        runAsNonRoot: true
"
            f"        runAsUser: 1000
"
            f"        fsGroup: 2000
"
            f"        seccompProfile:
"
            f"          type: RuntimeDefault
"
            f"      containers:
"
            f"      - name: varex-{inp.workload_type}
"
            f"        image: <IMAGE>:<TAG>
"
            f"        imagePullPolicy: IfNotPresent
"
            f"        securityContext:
"
            f"          allowPrivilegeEscalation: false
"
            f"          readOnlyRootFilesystem: true
"
            f"          capabilities:
"
            f"            drop: ["ALL"]
"
            f"{resources_block}"
            f"{probe_block}"
            f"        volumeMounts:
"
            f"        - name: tmp
"
            f"          mountPath: /tmp
"
            f"      volumes:
"
            f"      - name: tmp
"
            f"        emptyDir: {{}}
"
        )

    def _render_hpa(self) -> str:
        inp = self.inp
        if not inp.enable_hpa or inp.workload_type in ("database", "cache"):
            return (
                "# HPA not generated:
"
                f"# workload_type={inp.workload_type} — stateful workloads should not use HPA.
"
                "# Scale StatefulSets manually or via KEDA (event-driven).
"
            )
        return (
            f"---
apiVersion: autoscaling/v2
"
            f"kind: HorizontalPodAutoscaler
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}-hpa
"
            f"  namespace: {inp.namespace}
"
            f"spec:
"
            f"  scaleTargetRef:
"
            f"    apiVersion: apps/v1
"
            f"    kind: Deployment
"
            f"    name: varex-{inp.workload_type}
"
            f"  minReplicas: {self._hpa_min()}
"
            f"  maxReplicas: {self._hpa_max()}
"
            f"  metrics:
"
            f"  - type: Resource
"
            f"    resource:
"
            f"      name: cpu
"
            f"      target:
"
            f"        type: Utilization
"
            f"        averageUtilization: {self._hpa_cpu_target()}
"
            f"  - type: Resource
"
            f"    resource:
"
            f"      name: memory
"
            f"      target:
"
            f"        type: Utilization
"
            f"        averageUtilization: 80
"
            f"  behavior:
"
            f"    scaleDown:
"
            f"      stabilizationWindowSeconds: 300
"
            f"      policies:
"
            f"      - type: Pods
"
            f"        value: 1
"
            f"        periodSeconds: 60
"
            f"    scaleUp:
"
            f"      stabilizationWindowSeconds: 30
"
            f"      policies:
"
            f"      - type: Pods
"
            f"        value: 4
"
            f"        periodSeconds: 60
"
        )

    def _render_pdb(self) -> str:
        inp = self.inp
        if not inp.enable_pdb:
            return "# PDB not generated: enable_pdb=False
"
        min_avail = self._pdb_min_available()
        return (
            f"---
apiVersion: policy/v1
"
            f"kind: PodDisruptionBudget
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}-pdb
"
            f"  namespace: {inp.namespace}
"
            f"spec:
"
            f"  minAvailable: {min_avail}
"
            f"  selector:
"
            f"    matchLabels:
"
            f"      app: varex-{inp.workload_type}
"
        )

    def _render_netpol(self) -> str:
        inp = self.inp
        if not inp.enable_network_policy:
            return "# NetworkPolicy not generated: enable_network_policy=False
"
        return (
            f"---
# Deny all ingress/egress by default
"
            f"apiVersion: networking.k8s.io/v1
"
            f"kind: NetworkPolicy
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}-deny-all
"
            f"  namespace: {inp.namespace}
"
            f"spec:
"
            f"  podSelector:
"
            f"    matchLabels:
"
            f"      app: varex-{inp.workload_type}
"
            f"  policyTypes:
"
            f"  - Ingress
"
            f"  - Egress
"
            f"---
# Allow ingress from same namespace only
"
            f"apiVersion: networking.k8s.io/v1
"
            f"kind: NetworkPolicy
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}-allow-ingress
"
            f"  namespace: {inp.namespace}
"
            f"spec:
"
            f"  podSelector:
"
            f"    matchLabels:
"
            f"      app: varex-{inp.workload_type}
"
            f"  policyTypes:
"
            f"  - Ingress
"
            f"  ingress:
"
            f"  - from:
"
            f"    - namespaceSelector:
"
            f"        matchLabels:
"
            f"          kubernetes.io/metadata.name: {inp.namespace}
"
            f"  - ports:
"
            f"    - protocol: TCP
"
            f"      port: 8080
"
            f"---
# Allow DNS egress
"
            f"apiVersion: networking.k8s.io/v1
"
            f"kind: NetworkPolicy
"
            f"metadata:
"
            f"  name: varex-{inp.workload_type}-allow-dns
"
            f"  namespace: {inp.namespace}
"
            f"spec:
"
            f"  podSelector:
"
            f"    matchLabels:
"
            f"      app: varex-{inp.workload_type}
"
            f"  policyTypes:
"
            f"  - Egress
"
            f"  egress:
"
            f"  - ports:
"
            f"    - protocol: UDP
"
            f"      port: 53
"
            f"    - protocol: TCP
"
            f"      port: 53
"
        )

    # ── param builder ─────────────────────────────────────────────────────────

    def _build_params(self) -> list:
        inp       = self.inp
        p         = self._p
        ex        = inp.existing
        qos       = self._qos()
        req_cpu   = self._cpu_req()
        lim_cpu   = self._cpu_lim()
        req_mem   = self._mem_req()
        lim_mem   = self._mem_lim()
        hpa_min   = self._hpa_min()
        hpa_max   = self._hpa_max()
        hpa_tgt   = self._hpa_cpu_target()
        pdb_min   = self._pdb_min_available()
        pt        = self._probe_timeout()

        params = [

            # ── MAJOR ─────────────────────────────────────────────────────
            p(
                "CPU request", f"{req_cpu}m", M,
                f"cpu.requests = {req_cpu}m = {inp.container_cpu_cores} cores × 1000. "
                "Scheduler uses requests for bin-packing — a Pod without requests "
                "gets scheduled anywhere and can starve. "
                "CPU requests = guaranteed CPU share under contention (CFS). "
                "Too high: wastes node capacity (pods can't be scheduled). "
                "Too low: CPU throttling under load even when node has free capacity.",
                f"requests:
  cpu: {req_cpu}m",
                f"{ex.cpu_request_m}m" if ex.cpu_request_m else "NOT SET",
                safe=not bool(ex.cpu_request_m),
            ),
            p(
                "CPU limit", f"{lim_cpu}m" if lim_cpu else "none (BestEffort)", M,
                f"cpu.limits = {lim_cpu}m. "
                + (
                    f"Guaranteed QoS: limit = request = {req_cpu}m. "
                    "No CPU burst allowed — predictable latency, no noisy neighbour."
                    if qos == "Guaranteed" else
                    f"Burstable: limit = {lim_cpu}m = 2× request. "
                    "Container can burst to 2× cpu when node has spare capacity. "
                    "WARNING: CPU limits cause CFS throttling even when node is idle. "
                    "Consider omitting CPU limits for latency-sensitive workloads "
                    "(set only requests, rely on HPA for scaling). "
                    "NEVER omit memory limits — memory leak = OOM kill without limit."
                    if qos == "Burstable" else
                    "BestEffort: no limit. Evicted first under resource pressure."
                ),
                f"limits:
  cpu: {lim_cpu}m" if lim_cpu else "# no cpu limit",
                f"{ex.cpu_limit_m}m" if ex.cpu_limit_m else None,
                safe=False,
            ),
            p(
                "Memory request", f"{req_mem}Mi", M,
                f"memory.requests = {req_mem}Mi = {inp.container_ram_gb}GB. "
                "Memory requests: guaranteed allocation, affects scheduling. "
                "OOM eviction order: BestEffort first, then Burstable (furthest over request), "
                "then Guaranteed. "
                "Always set memory requests = memory limits for database/cache (Guaranteed QoS).",
                f"requests:
  memory: {req_mem}Mi",
                f"{ex.memory_request_mb}Mi" if ex.memory_request_mb else "NOT SET",
                safe=not bool(ex.memory_request_mb),
            ),
            p(
                "Memory limit", f"{lim_mem}Mi" if lim_mem else "none", M,
                f"memory.limits = {lim_mem}Mi. "
                "When container exceeds memory limit: OOM killer sends SIGKILL immediately. "
                + (
                    "database: limit = request (no burst). "
                    "Memory burst for databases causes: eviction pressure, "
                    "swapping on node, latency spikes."
                    if inp.workload_type in ("database", "cache") else
                    f"Burstable: {lim_mem}Mi = {req_mem}Mi × 1.5. "
                    "50% burst headroom for traffic spikes. "
                    "ALWAYS set memory limits — without them a memory leak "
                    "consumes all node RAM and triggers node-level OOM."
                ),
                f"limits:
  memory: {lim_mem}Mi" if lim_mem else "# no memory limit — dangerous",
                f"{ex.memory_limit_mb}Mi" if ex.memory_limit_mb else "NOT SET",
                safe=not bool(ex.memory_limit_mb),
            ),
            p(
                "QoS class", qos, M,
                {
                    "Guaranteed": (
                        "Guaranteed QoS: requests == limits for ALL containers. "
                        "Pod is never throttled, never evicted unless system critical. "
                        "Required for: databases, caches, latency-critical services. "
                        "Scheduler: Guaranteed pods get dedicated CPU/memory — no overcommit."
                    ),
                    "Burstable": (
                        "Burstable QoS: requests < limits. "
                        "Pod guaranteed minimum (requests), can burst to limits. "
                        "Evicted after BestEffort pods when node is under pressure. "
                        "Best for: web/worker workloads with variable CPU/memory patterns."
                    ),
                    "BestEffort": (
                        "BestEffort QoS: no requests or limits. "
                        "First to be evicted under ANY resource pressure. "
                        "Only suitable for: truly non-critical batch jobs. "
                        "NEVER use for web-facing or stateful workloads."
                    ),
                }.get(qos, ""),
                f"# QoS={qos}: requests={'=limits' if qos=='Guaranteed' else '<limits'}",
                ex.qos_class,
                safe=False,
            ),
            p(
                "replicas", str(inp.replicas), M,
                f"Replica count = {inp.replicas}. "
                + (
                    "Single replica: any pod crash, node drain, or rolling update "
                    "causes complete downtime. Minimum 2 replicas for HA. "
                    "Minimum 3 replicas for proper PodDisruptionBudget + zone spread."
                    if inp.replicas < 2 else
                    f"{inp.replicas} replicas across nodes with podAntiAffinity "
                    "ensures no single node failure causes downtime. "
                    "terminationGracePeriodSeconds=60 ensures in-flight requests complete "
                    "during rolling updates."
                ),
                f"replicas: {inp.replicas}",
                str(ex.replicas) if ex.replicas else None,
                safe=False,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "Liveness probe", "enabled", MED,
                "livenessProbe: kubelet kills + restarts container if probe fails 3× consecutively. "
                "Without liveness probe: deadlocked container serves 0 RPS but stays Running. "
                "initialDelaySeconds=30: avoids killing container during JVM/app startup. "
                f"timeoutSeconds={pt}: must be > avg_request_ms ({inp.avg_request_ms}ms).",
                f"livenessProbe:
  httpGet: {{path: /healthz, port: 8080}}
"
                f"  initialDelaySeconds: 30
  timeoutSeconds: {pt}",
            ) if inp.workload_type != "batch" else None,
            p(
                "Readiness probe", "enabled", MED,
                "readinessProbe: removes pod from Service endpoints if probe fails. "
                "Without readiness probe: pod receives traffic before app is ready "
                "(during startup, after config reload). "
                "First 503s during rolling deployment. "
                "Critical for zero-downtime deployments.",
                f"readinessProbe:
  httpGet: {{path: /ready, port: 8080}}
"
                f"  periodSeconds: 5
  failureThreshold: 3
  timeoutSeconds: {pt}",
            ) if inp.workload_type != "batch" else None,
            p(
                "Startup probe", "enabled", MED,
                "startupProbe: delays liveness probe until app passes startup check. "
                "failureThreshold=30 × periodSeconds=10 = 5 minutes max startup time. "
                "Without startup probe: liveness probe kills slow-starting app (JVM warm-up, "
                "database migration, large model loading) before it finishes starting.",
                "startupProbe:
  httpGet: {path: /healthz, port: 8080}
"
                "  failureThreshold: 30
  periodSeconds: 10",
            ) if inp.workload_type != "batch" else None,
            p(
                "HPA (HorizontalPodAutoscaler)", f"min={hpa_min} max={hpa_max} cpu={hpa_tgt}%", MED,
                f"HPA: scales from {hpa_min} to {hpa_max} replicas based on CPU utilisation. "
                f"Target CPU = {hpa_tgt}% — triggers scale-up when average CPU across pods "
                f"exceeds {hpa_tgt}%. "
                "scaleDown.stabilizationWindow=300s: prevents thrashing during traffic dips. "
                "scaleUp: max 4 pods/minute to avoid thundering herd on upstream. "
                "Memory metric added (80% target) for memory-bound workloads.",
                f"HPA minReplicas={hpa_min} maxReplicas={hpa_max} cpuTarget={hpa_tgt}%",
                f"enabled={ex.hpa_enabled}" if ex.hpa_enabled is not None else None,
            ) if inp.enable_hpa and inp.workload_type not in ("database", "cache") else None,
            p(
                "PodDisruptionBudget", f"minAvailable={pdb_min}", MED,
                f"PDB ensures at least {pdb_min} pods remain available during voluntary disruptions "
                f"(node drain for maintenance, cluster upgrade). "
                f"minAvailable = max(1, ceil({inp.replicas} × 0.5)) = {pdb_min}. "
                "Without PDB: kubectl drain can terminate ALL pods simultaneously → downtime.",
                f"minAvailable: {pdb_min}",
                f"enabled={ex.pdb_enabled}" if ex.pdb_enabled is not None else None,
            ) if inp.enable_pdb else None,
            p(
                "podAntiAffinity", "preferredDuringScheduling", MED,
                "Spread pods across different nodes (topology: kubernetes.io/hostname). "
                "Without anti-affinity: scheduler may place all replicas on same node "
                "→ node failure kills all replicas simultaneously.",
                "affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution",
            ),
            p(
                "topologySpreadConstraints", "maxSkew=1", MED,
                "Spread pods evenly across nodes/zones. "
                "maxSkew=1: difference in pod count between any two nodes ≤ 1. "
                "whenUnsatisfiable=DoNotSchedule: strict enforcement. "
                "Stronger than podAntiAffinity for multi-zone clusters.",
                "topologySpreadConstraints:
- maxSkew: 1
  topologyKey: kubernetes.io/hostname",
            ) if inp.workload_type not in ("database", "cache") else None,
            p(
                "readOnlyRootFilesystem", "true", MED,
                "Container root filesystem read-only. "
                "Prevents runtime writes to container layers — "
                "malware cannot persist to image. "
                "Pair with emptyDir volume for /tmp. "
                "CIS Kubernetes Benchmark 5.7.3: required.",
                "securityContext:
  readOnlyRootFilesystem: true",
                safe=False,
            ),
            p(
                "runAsNonRoot + runAsUser=1000", "enabled", MED,
                "Pod runs as non-root UID 1000. "
                "Without: container runs as UID 0 (root) in the container, "
                "which maps to root on node if namespace escapes. "
                "runAsNonRoot=true: kubelet rejects container if image runs as UID 0. "
                "CIS Benchmark 5.7.1: required.",
                "securityContext:
  runAsNonRoot: true
  runAsUser: 1000",
                safe=False,
            ),
            p(
                "capabilities drop ALL", "enabled", MED,
                "Drop all Linux capabilities in container. "
                "Default container retains ~14 capabilities. "
                "Only NET_BIND_SERVICE retained (bind port < 1024). "
                "CIS Benchmark 5.7.5: required.",
                "capabilities:
  drop: ["ALL"]",
                safe=False,
            ),
            p(
                "automountServiceAccountToken", "false", MED,
                "Default: Kubernetes auto-mounts ServiceAccount token as volume. "
                "Any container process can use the token to call kube-apiserver. "
                "Disable unless container explicitly needs API access. "
                "RBAC escape risk: compromised container → API token → cluster-wide access.",
                "automountServiceAccountToken: false",
                safe=False,
            ),
            p(
                "terminationGracePeriodSeconds", "60s", MED,
                "Time kubelet waits for container to exit gracefully (SIGTERM → SIGKILL). "
                "Default 30s — too short for: slow DB shutdown, in-flight request drain, "
                f"avg_request_ms={inp.avg_request_ms}ms with queued backlog. "
                "60s allows: active connections to drain, DB WAL flush, cache flush.",
                "terminationGracePeriodSeconds: 60",
            ),
            p(
                "NetworkPolicy (deny-all default)", "enabled", MED,
                "Default Kubernetes: all pods can talk to all pods in cluster. "
                "deny-all NetworkPolicy: blocks all ingress + egress by default. "
                "allow-ingress: only same-namespace pods can reach this service on port 8080. "
                "allow-dns: UDP 53 egress for CoreDNS resolution. "
                "Zero-trust network model — critical for PCI/HIPAA compliance.",
                "# See network_policy_yaml in response",
            ) if inp.enable_network_policy else None,
        ]

        params += [
            p(
                "imagePullPolicy", "IfNotPresent", MIN,
                "IfNotPresent: use cached image if available. "
                "Default Always: pulls image on every pod start → slow startup + registry dependency. "
                "Use Always only for mutable tags (latest). "
                "Best practice: use immutable image tags (SHA digest or semver).",
                "imagePullPolicy: IfNotPresent",
                ex.image_pull_policy,
            ),
            p(
                "seccompProfile RuntimeDefault", "enabled", MIN,
                "seccomp RuntimeDefault: applies container runtime default syscall filter. "
                "Blocks ~300 dangerous syscalls (ptrace, mount, etc.). "
                "Kubernetes 1.27+: RuntimeDefault enabled by default for new pods. "
                "CIS Benchmark 5.7.2: required.",
                "seccompProfile:
  type: RuntimeDefault",
                safe=False,
            ),
            p(
                "HPA scaleDown stabilization", "300s", MIN,
                "stabilizationWindowSeconds=300: HPA waits 5min before scaling down. "
                "Prevents scale-down thrashing: brief traffic dip → scale down → "
                "traffic recovers → scale up → repeat. "
                "5min window smooths normal traffic variance.",
                "behavior:
  scaleDown:
    stabilizationWindowSeconds: 300",
            ) if inp.enable_hpa else None,
        ]

        return [x for x in params if x is not None]

    # ── audit (EXISTING mode) ─────────────────────────────────────────────────

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if not ex.cpu_request_m:
            findings.append(
                "[MAJOR] cpu.requests NOT SET → BestEffort QoS. "
                "Pod evicted first under any CPU pressure. "
                f"Recommended: cpu.requests={self._cpu_req()}m"
            )
        if not ex.memory_request_mb:
            findings.append(
                "[MAJOR] memory.requests NOT SET → BestEffort QoS. "
                f"Recommended: memory.requests={self._mem_req()}Mi"
            )
        if not ex.memory_limit_mb:
            findings.append(
                "[MAJOR] memory.limits NOT SET. Memory leak consumes all node RAM → node OOM. "
                f"Recommended: memory.limits={self._mem_lim()}Mi"
            )
        if ex.qos_class == "BestEffort" and self.inp.workload_type in ("web", "database", "cache"):
            findings.append(
                f"[MAJOR] QoS=BestEffort for workload_type={self.inp.workload_type}. "
                "BestEffort pods are evicted first. Set requests + limits for Burstable/Guaranteed."
            )
        if ex.replicas == 1:
            findings.append(
                "[MAJOR] replicas=1 — single point of failure. "
                "Node drain, pod crash, or rolling update causes complete downtime. "
                "Minimum 2 replicas for HA. Recommended 3."
            )
        if not ex.liveness_probe and self.inp.workload_type != "batch":
            findings.append(
                "[MAJOR] livenessProbe NOT SET. Deadlocked container stays Running. "
                "kubelet cannot detect hung application without probe."
            )
        if not ex.readiness_probe and self.inp.workload_type != "batch":
            findings.append(
                "[MAJOR] readinessProbe NOT SET. Pod receives traffic before app is ready. "
                "Rolling deployments will cause 503s on startup."
            )
        if not ex.hpa_enabled and self.inp.workload_type in ("web", "worker"):
            findings.append(
                "[MEDIUM] HPA NOT enabled. Static replica count cannot handle traffic bursts. "
                f"Recommended: HPA min={self._hpa_min()} max={self._hpa_max()} "
                f"cpuTarget={self._hpa_cpu_target()}%"
            )
        if not ex.pdb_enabled and self.inp.replicas > 1:
            findings.append(
                "[MEDIUM] PodDisruptionBudget NOT set. "
                "kubectl drain can terminate ALL pods simultaneously during node maintenance."
            )
        if not ex.topology_spread and self.inp.replicas > 1:
            findings.append(
                "[MEDIUM] topologySpreadConstraints NOT set. "
                "Scheduler may co-locate all replicas on same node → node failure = downtime."
            )
        if ex.image_pull_policy == "Always":
            findings.append(
                "[MEDIUM] imagePullPolicy=Always. "
                "Every pod start pulls image from registry. "
                "Registry outage = pod start failure. Use IfNotPresent with immutable tags."
            )

        return findings

    # ── public entry point ────────────────────────────────────────────────────

    def generate(self) -> K8sOutput:
        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.node_cpu_cores,
            ram_gb    = self.inp.node_ram_gb,
            max_conns = self.inp.replicas * 1000,
            os_type   = self.inp.os_type,
            existing  = {},
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        return K8sOutput(
            mode                    = self.inp.mode,
            cpu_request_m           = self._cpu_req(),
            cpu_limit_m             = self._cpu_lim(),
            memory_request_mb       = self._mem_req(),
            memory_limit_mb         = self._mem_lim(),
            effective_qos_class     = self._qos(),
            recommended_replicas    = self.inp.replicas,
            hpa_min_replicas        = self._hpa_min(),
            hpa_max_replicas        = self._hpa_max(),
            hpa_cpu_target_percent  = self._hpa_cpu_target(),
            deployment_yaml         = self._render_deployment(),
            hpa_yaml                = self._render_hpa(),
            pdb_yaml                = self._render_pdb(),
            network_policy_yaml     = self._render_netpol(),
            major_params            = major,
            medium_params           = medium,
            minor_params            = minor,
            os_sysctl_conf          = os_engine.sysctl_block(),
            ha_suggestions=[
                "Deploy across ≥ 3 availability zones with topologySpreadConstraints zone key.",
                "Use Cluster Autoscaler (CA) or Karpenter to add/remove nodes as HPA scales pods.",
                "Database workloads: use StatefulSet + PVC with ReadWriteOnce + StorageClass with "
                "WaitForFirstConsumer binding for zone-aware volume placement.",
                "Ingress: use NGINX Ingress Controller + cert-manager for TLS + HPA for ingress pods.",
                "Observability: Prometheus PodMonitor + Grafana dashboard per workload type. "
                "Alert on: cpu throttling ratio > 10%, memory working set > 80% of limit.",
                "Use Vertical Pod Autoscaler (VPA) in 'Off' mode to get right-sizing recommendations "
                "without automatic restarts.",
            ],
            performance_warnings=[w for w in [
                (f"cpu_limit ({self._cpu_lim()}m) = 2× cpu_request ({self._cpu_req()}m). "
                 "CFS throttling will occur even when node has spare CPU. "
                 "Consider setting only cpu.requests and relying on HPA.")
                if self._qos() == "Burstable" and self.inp.workload_type == "web" else None,
                ("replicas=1: single point of failure. Set replicas ≥ 2.")
                if self.inp.replicas < 2 else None,
                ("database workload with HPA: stateful workloads should use StatefulSet "
                 "with manual scaling or KEDA, not CPU-based HPA.")
                if self.inp.workload_type in ("database", "cache") and self.inp.enable_hpa else None,
            ] if w],
            capacity_warning        = self._capacity_warning(
                self.inp.replicas, int(self.inp.node_ram_gb / self.inp.container_ram_gb),
                "node capacity"
            ),
            audit_findings          = self._audit()
                                      if self.inp.mode == CalcMode.EXISTING else [],
        )
