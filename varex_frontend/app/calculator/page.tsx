"use client";

import { useMemo, useState } from "react";
import { Calculator, Loader2, Play, RefreshCcw, AlertTriangle, Terminal, FileCode, ChevronDown, ChevronUp } from "lucide-react";
import { getCalculatorExample, runCalculator } from "@/lib/api";

/* ════════════════════════════════════════════════════════
   Types
   ════════════════════════════════════════════════════════ */
type FieldType = "number" | "text" | "boolean" | "select";
type FieldConfig = {
  key: string; label: string; type: FieldType;
  required?: boolean; min?: number; max?: number; step?: number;
  placeholder?: string; options?: string[];
};
type CalcConfig = {
  key: string; label: string;
  profiles: { key: string; label: string }[];
  fields: FieldConfig[];
};

/* ════════════════════════════════════════════════════════
   OS Types
   ════════════════════════════════════════════════════════ */
const OS_TYPES = [
  "RHEL", "CentOS", "Ubuntu", "Debian", "Amazon Linux", "SUSE/SLES",
  "Oracle Linux", "Rocky Linux", "AlmaLinux", "Fedora",
  "Windows Server 2022", "Windows Server 2019", "Windows Server 2016",
  "Solaris 11", "Solaris 10", "AIX 7.3", "AIX 7.2", "HP-UX 11i v3",
];

/* ════════════════════════════════════════════════════════
   Common smart inputs every calculator gets
   ════════════════════════════════════════════════════════ */
const COMMON: FieldConfig[] = [
  { key: "mode", label: "Mode", type: "select", options: ["new", "existing"], required: true },
  { key: "os_type", label: "Operating System", type: "select", options: OS_TYPES, required: true },
  { key: "cpu_cores", label: "CPU Cores", type: "number", min: 1, step: 1, required: true },
  { key: "ram_gb", label: "RAM (GB)", type: "number", min: 1, step: 1, required: true },
  { key: "expected_rps", label: "Expected RPS", type: "number", min: 1, step: 1, required: true },
  { key: "avg_response_ms", label: "Avg Response (ms)", type: "number", min: 1, step: 1, required: true },
];

/* ════════════════════════════════════════════════════════
   Per-calculator SMART INPUT fields
   (fewer inputs → engine computes everything)
   ════════════════════════════════════════════════════════ */
const CALCULATORS: CalcConfig[] = [
  {
    key: "nginx", label: "NGINX",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "avg_response_kb", label: "Avg Response Size (KB)", type: "number", min: 1, step: 1, placeholder: "50" },
    { key: "ssl_enabled", label: "SSL/TLS Enabled?", type: "boolean" },
    { key: "reverse_proxy", label: "Reverse Proxy Mode?", type: "boolean" },
    { key: "static_pct", label: "Static Content %", type: "number", min: 0, max: 100, step: 5, placeholder: "20" },
    { key: "keepalive_enabled", label: "Keepalive Enabled?", type: "boolean" },
    { key: "gzip_enabled", label: "Gzip Compression?", type: "boolean" },
    { key: "http2_enabled", label: "HTTP/2 Enabled?", type: "boolean" },
    { key: "client_max_body_size_mb", label: "Max Upload (MB)", type: "number", min: 1, step: 1, placeholder: "10" },
    ],
  },
  {
    key: "redis", label: "Redis",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "estimated_keys", label: "Estimated Keys", type: "number", min: 1, step: 1, placeholder: "1000000" },
    { key: "avg_key_size_bytes", label: "Avg Key+Value Size (bytes)", type: "number", min: 64, step: 64, placeholder: "512" },
    { key: "persistence_type", label: "Persistence", type: "select", options: ["aof", "rdb", "none"] },
    { key: "cluster_enabled", label: "Cluster Mode?", type: "boolean" },
    { key: "password_enabled", label: "Require Auth?", type: "boolean" },
    ],
  },
  {
    key: "tomcat", label: "Tomcat",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "app_type", label: "App Type", type: "select", options: ["rest", "webapp", "microservice"] },
    { key: "ssl_enabled", label: "SSL/TLS?", type: "boolean" },
    { key: "max_upload_mb", label: "Max Upload (MB)", type: "number", min: 1, step: 1, placeholder: "50" },
    { key: "session_timeout_min", label: "Session Timeout (min)", type: "number", min: 1, step: 1, placeholder: "30" },
    { key: "enable_compression", label: "HTTP Compression?", type: "boolean" },
    { key: "jmx_enabled", label: "JMX Monitoring?", type: "boolean" },
    ],
  },
  {
    key: "httpd", label: "Apache HTTPD",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "ssl_enabled", label: "SSL/TLS?", type: "boolean" },
    { key: "mpm_type", label: "MPM Type", type: "select", options: ["event", "worker", "prefork"] },
    { key: "server_limit", label: "Server Limit", type: "number", min: 1, step: 1, placeholder: "16" },
    { key: "enable_mod_deflate", label: "mod_deflate?", type: "boolean" },
    ],
  },
  {
    key: "ohs", label: "Oracle HTTP Server",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "ssl_enabled", label: "SSL/TLS?", type: "boolean" },
    { key: "max_clients", label: "Max Clients", type: "number", min: 100, step: 1, placeholder: "1000" },
    ],
  },
  {
    key: "ihs", label: "IBM HTTP Server",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "ssl_enabled", label: "SSL/TLS?", type: "boolean" },
    { key: "max_request_workers", label: "Max Request Workers", type: "number", min: 100, step: 1, placeholder: "1000" },
    ],
  },
  {
    key: "iis", label: "IIS",
    profiles: [{ key: "new-core", label: "New .NET Core" }, { key: "new-fx", label: "New .NET Framework" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "dotnet_type", label: ".NET Type", type: "select", options: ["core", "framework"] },
    { key: "ssl_enabled", label: "SSL/TLS?", type: "boolean" },
    { key: "enable_compression", label: "Compression?", type: "boolean" },
    { key: "enable_caching", label: "Output Caching?", type: "boolean" },
    ],
  },
  {
    key: "postgresql", label: "PostgreSQL",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, placeholder: "300" },
    { key: "disk_type", label: "Disk Type", type: "select", options: ["ssd", "hdd", "nvme"] },
    { key: "workload", label: "Workload", type: "select", options: ["oltp", "olap", "mixed"] },
    { key: "wal_level", label: "WAL Level", type: "select", options: ["replica", "minimal", "logical"] },
    { key: "ssl_enabled", label: "SSL?", type: "boolean" },
    ],
  },
  {
    key: "mysql", label: "MySQL",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, placeholder: "300" },
    { key: "disk_type", label: "Disk Type", type: "select", options: ["ssd", "hdd", "nvme"] },
    { key: "workload", label: "Workload", type: "select", options: ["oltp", "olap", "mixed"] },
    { key: "replication", label: "Replication?", type: "boolean" },
    { key: "ssl_enabled", label: "SSL?", type: "boolean" },
    ],
  },
  {
    key: "mongodb", label: "MongoDB",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, placeholder: "500" },
    { key: "disk_type", label: "Disk Type", type: "select", options: ["ssd", "hdd", "nvme"] },
    { key: "replica_set", label: "Replica Set?", type: "boolean" },
    { key: "sharding", label: "Sharding?", type: "boolean" },
    { key: "auth_enabled", label: "Auth Enabled?", type: "boolean" },
    ],
  },
  {
    key: "haproxy", label: "HAProxy",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "backends_count", label: "Backend Servers", type: "number", min: 1, step: 1, placeholder: "5" },
    { key: "ssl_termination", label: "SSL Termination?", type: "boolean" },
    { key: "http_mode", label: "HTTP Mode?", type: "boolean" },
    { key: "health_check_interval_s", label: "Health Check (s)", type: "number", min: 1, step: 1, placeholder: "5" },
    ],
  },
  {
    key: "k8s", label: "Kubernetes",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1, placeholder: "3" },
    { key: "workload_type", label: "Workload", type: "select", options: ["web", "database", "worker", "mixed"] },
    { key: "hpa_enabled", label: "HPA Auto-Scaling?", type: "boolean" },
    { key: "pdb_enabled", label: "PDB (Disruption Budget)?", type: "boolean" },
    { key: "ingress_enabled", label: "Ingress?", type: "boolean" },
    ],
  },
  {
    key: "docker", label: "Docker",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "workload_type", label: "Workload", type: "select", options: ["web", "database", "worker", "mixed"] },
    { key: "compose", label: "Docker Compose?", type: "boolean" },
    { key: "swarm", label: "Swarm Mode?", type: "boolean" },
    ],
  },
  {
    key: "podman", label: "Podman",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1, placeholder: "2" },
    { key: "workload_type", label: "Workload", type: "select", options: ["web", "database", "worker"] },
    { key: "rootless", label: "Rootless Mode?", type: "boolean" },
    ],
  },
  {
    key: "os", label: "Linux OS",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "workload_type", label: "Workload", type: "select", options: ["web", "database", "mixed", "compute", "storage"] },
    { key: "disk_type", label: "Disk Type", type: "select", options: ["ssd", "hdd", "nvme"] },
    ],
  },
  {
    key: "rabbitmq", label: "RabbitMQ",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON,
    { key: "queue_count", label: "Queue Count", type: "number", min: 1, step: 1, placeholder: "200" },
    { key: "consumers", label: "Consumers", type: "number", min: 1, step: 1, placeholder: "50" },
    { key: "cluster_enabled", label: "Cluster?", type: "boolean" },
    { key: "ssl_enabled", label: "SSL?", type: "boolean" },
    ],
  },
];

/* ════════════════════════════════════════════════════════
   impact badge colors
   ════════════════════════════════════════════════════════ */
const BADGE: Record<string, string> = {
  MAJOR: "bg-rose-500/20 text-rose-300 border-rose-500/30",
  MEDIUM: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  MINOR: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  DEGRADATION: "bg-red-600/20 text-red-300 border-red-600/40",
};

/* ════════════════════════════════════════════════════════
   Component
   ════════════════════════════════════════════════════════ */
export default function CalculatorPage() {
  const [calculator, setCalculator] = useState(CALCULATORS[0].key);
  const [profile, setProfile] = useState(CALCULATORS[0].profiles[0].key);
  const [values, setValues] = useState<Record<string, string | number | boolean>>({
    mode: "new", os_type: "RHEL", cpu_cores: 8, ram_gb: 32, expected_rps: 10000, avg_response_ms: 120,
  });
  const [loadingExample, setLoadingExample] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);
  const [expandSnippet, setExpandSnippet] = useState(true);
  const [expandOS, setExpandOS] = useState(true);

  const selected = useMemo(() => CALCULATORS.find((c) => c.key === calculator) ?? CALCULATORS[0], [calculator]);
  const setValue = (key: string, val: string | number | boolean) => setValues((prev) => ({ ...prev, [key]: val }));

  const loadExample = async () => {
    setLoadingExample(true); setError("");
    try {
      const data = await getCalculatorExample(calculator, profile);
      if (data && typeof data === "object") setValues(data as Record<string, string | number | boolean>);
    } catch (e: any) { setError(e?.detail ?? e?.message ?? "Failed."); }
    finally { setLoadingExample(false); }
  };

  const run = async () => {
    setLoadingRun(true); setError("");
    try {
      const payload: Record<string, unknown> = {};
      for (const f of selected.fields) {
        const raw = values[f.key];
        if (raw === undefined || raw === "") continue;
        if (f.type === "number") payload[f.key] = Number(raw);
        else if (f.type === "boolean") payload[f.key] = Boolean(raw);
        else payload[f.key] = raw;
      }
      payload.calculator = calculator;
      const data = await runCalculator(calculator, payload);
      setResult(data);
    } catch (e: any) { setError(e?.detail ?? e?.message ?? "Failed."); }
    finally { setLoadingRun(false); }
  };

  // ── group params by impact ──
  const majorParams = result?.recommended_params?.filter((p: any) => p.impact === "MAJOR") ?? [];
  const mediumParams = result?.recommended_params?.filter((p: any) => p.impact === "MEDIUM") ?? [];
  const minorParams = result?.recommended_params?.filter((p: any) => p.impact === "MINOR") ?? [];
  const degradations = result?.degradation_params ?? [];
  const capacityWarnings = result?.capacity_warnings ?? [];
  const configSnippet = result?.config_snippet ?? "";
  const osTuning = result?.os_tuning ?? null;
  const audit = result?.audit_findings ?? [];

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-300"><Calculator className="h-5 w-5" /></div>
          <div>
            <h1 className="text-xl font-bold text-white">Smart Production Calculator</h1>
            <p className="text-sm text-slate-400">Enter key inputs → Engine computes all recommended parameters</p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
          {/* ── Sidebar ── */}
          <aside className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Calculator</p>
            <div className="space-y-1.5 max-h-[70vh] overflow-y-auto">
              {CALCULATORS.map((c) => (
                <button key={c.key} type="button"
                  onClick={() => { setCalculator(c.key); setProfile(c.profiles[0].key); setError(""); setResult(null); }}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition-all ${calculator === c.key
                    ? "border-cyan-500/70 bg-cyan-500/10 text-cyan-100 shadow-sm shadow-cyan-500/20"
                    : "border-slate-800 bg-slate-900 text-slate-300 hover:border-slate-700 hover:text-white"}`}
                >{c.label}</button>
              ))}
            </div>
          </aside>

          {/* ── Main panel ── */}
          <div className="space-y-5">
            {/* Profile + Load Example */}
            <div className="grid gap-3 sm:grid-cols-2 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Profile</span>
                <select value={profile} onChange={(e) => setProfile(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                  {selected.profiles.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
                </select>
              </label>
              <div className="flex items-end">
                <button type="button" onClick={loadExample} disabled={loadingExample}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm text-slate-100 disabled:opacity-60 hover:border-cyan-600 transition-colors">
                  {loadingExample ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
                  Load Example
                </button>
              </div>
            </div>

            {/* Smart Input Fields */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-cyan-400">⚙️ Smart Inputs</p>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {selected.fields.map((f) => (
                  <label key={f.key} className="flex flex-col gap-1.5">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{f.label}</span>
                    {f.type === "select" ? (
                      <select value={(values[f.key] ?? "").toString()} onChange={(e) => setValue(f.key, e.target.value)}
                        className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                        {(f.options ?? []).map((o) => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : f.type === "boolean" ? (
                      <div className="flex items-center gap-2 min-h-[38px]">
                        <input type="checkbox" checked={Boolean(values[f.key])} onChange={(e) => setValue(f.key, e.target.checked)}
                          className="h-5 w-5 rounded border-slate-600 accent-cyan-500" />
                        <span className="text-xs text-slate-400">{values[f.key] ? "Yes" : "No"}</span>
                      </div>
                    ) : (
                      <input type="number" value={(values[f.key] ?? "").toString()} placeholder={f.placeholder}
                        min={f.min} max={f.max} step={f.step}
                        onChange={(e) => setValue(f.key, e.target.value)}
                        className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
                    )}
                  </label>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-3">
                <button type="button" onClick={run} disabled={loadingRun}
                  className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 px-6 text-sm font-semibold text-white disabled:opacity-60 hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/20">
                  {loadingRun ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Compute Recommendations
                </button>
                {error && <p className="text-sm text-rose-400">{error}</p>}
              </div>
            </div>

            {/* ════ RESULTS ════ */}
            {result && (
              <div className="space-y-4">
                {/* Capacity Warnings */}
                {capacityWarnings.length > 0 && (
                  <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4">
                    <div className="flex items-center gap-2 mb-2"><AlertTriangle className="h-5 w-5 text-amber-400" /><span className="font-bold text-amber-300">Capacity Warnings</span></div>
                    {capacityWarnings.map((w: string, i: number) => <p key={i} className="text-sm text-amber-200">{w}</p>)}
                  </div>
                )}

                {/* DEGRADATION Section */}
                {degradations.length > 0 && (
                  <div className="rounded-xl border border-red-600/40 bg-red-600/10 p-4">
                    <p className="font-bold text-red-300 mb-2">⚠️ Potential Degradation Risks</p>
                    <div className="space-y-2">
                      {degradations.map((d: any, i: number) => (
                        <div key={i} className="rounded-lg border border-red-700/30 bg-red-950/40 p-3">
                          <p className="font-semibold text-red-200 text-sm">{d.name}</p>
                          <p className="text-xs text-red-300/80 mt-1">{d.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* MAJOR Params */}
                {majorParams.length > 0 && (
                  <div className="rounded-xl border border-rose-500/30 bg-slate-900/50 p-4">
                    <p className="font-bold text-rose-300 mb-3 text-sm uppercase tracking-widest">🔴 Major Parameters ({majorParams.length})</p>
                    <div className="grid gap-2 md:grid-cols-2">
                      {majorParams.map((p: any, i: number) => (
                        <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono text-sm text-white">{p.name}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${BADGE.MAJOR}`}>MAJOR</span>
                          </div>
                          <p className="font-mono text-cyan-300 text-sm">{p.recommended}</p>
                          <p className="text-xs text-slate-400 mt-1">{p.details}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* MEDIUM Params */}
                {mediumParams.length > 0 && (
                  <div className="rounded-xl border border-amber-500/30 bg-slate-900/50 p-4">
                    <p className="font-bold text-amber-300 mb-3 text-sm uppercase tracking-widest">🟡 Medium Parameters ({mediumParams.length})</p>
                    <div className="grid gap-2 md:grid-cols-2">
                      {mediumParams.map((p: any, i: number) => (
                        <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono text-sm text-white">{p.name}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${BADGE.MEDIUM}`}>MEDIUM</span>
                          </div>
                          <p className="font-mono text-cyan-300 text-sm">{p.recommended}</p>
                          <p className="text-xs text-slate-400 mt-1">{p.details}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* MINOR Params */}
                {minorParams.length > 0 && (
                  <div className="rounded-xl border border-slate-600/30 bg-slate-900/50 p-4">
                    <p className="font-bold text-slate-300 mb-3 text-sm uppercase tracking-widest">⚪ Minor Parameters ({minorParams.length})</p>
                    <div className="grid gap-2 md:grid-cols-2">
                      {minorParams.map((p: any, i: number) => (
                        <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono text-sm text-white">{p.name}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${BADGE.MINOR}`}>MINOR</span>
                          </div>
                          <p className="font-mono text-cyan-300 text-sm">{p.recommended}</p>
                          <p className="text-xs text-slate-400 mt-1">{p.details}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Config Snippet */}
                {configSnippet && (
                  <div className="rounded-xl border border-cyan-500/30 bg-slate-900/50 p-4">
                    <button onClick={() => setExpandSnippet(!expandSnippet)}
                      className="flex items-center justify-between w-full mb-2">
                      <span className="flex items-center gap-2 font-bold text-cyan-300 text-sm uppercase tracking-widest">
                        <FileCode className="h-4 w-4" /> Config Snippet
                      </span>
                      {expandSnippet ? <ChevronUp className="h-4 w-4 text-cyan-400" /> : <ChevronDown className="h-4 w-4 text-cyan-400" />}
                    </button>
                    {expandSnippet && (
                      <pre className="rounded-lg bg-slate-950 p-4 text-xs text-green-300 font-mono overflow-auto max-h-80 border border-slate-700">{configSnippet}</pre>
                    )}
                  </div>
                )}

                {/* OS Tuning */}
                {osTuning?.commands?.length > 0 && (
                  <div className="rounded-xl border border-amber-500/30 bg-slate-900/50 p-4">
                    <button onClick={() => setExpandOS(!expandOS)}
                      className="flex items-center justify-between w-full mb-2">
                      <span className="flex items-center gap-2 font-bold text-amber-300 text-sm uppercase tracking-widest">
                        <Terminal className="h-4 w-4" /> OS Tuning Commands ({osTuning.os_type})
                      </span>
                      {expandOS ? <ChevronUp className="h-4 w-4 text-amber-400" /> : <ChevronDown className="h-4 w-4 text-amber-400" />}
                    </button>
                    {expandOS && (
                      <pre className="rounded-lg bg-slate-950 p-4 text-xs text-amber-200 font-mono overflow-auto max-h-60 border border-slate-700">
                        {osTuning.commands.join("\n")}
                      </pre>
                    )}
                  </div>
                )}

                {/* Audit Findings */}
                {audit.length > 0 && (
                  <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
                    <p className="font-bold text-slate-300 mb-2 text-sm uppercase tracking-widest">📋 Audit Notes</p>
                    <ul className="list-disc list-inside space-y-1">
                      {audit.map((a: string, i: number) => <li key={i} className="text-xs text-slate-400">{a}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
