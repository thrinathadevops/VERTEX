"use client";

import { useMemo, useState } from "react";
import { Calculator, Loader2, Play, RefreshCcw } from "lucide-react";
import { getCalculatorExample, runCalculator } from "@/lib/api";

type FieldType = "number" | "text" | "boolean" | "select";

type FieldConfig = {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  options?: string[];
};

type CalculatorConfig = {
  key: string;
  label: string;
  profiles: { key: string; label: string }[];
  fields: FieldConfig[];
};

const COMMON_FIELDS: FieldConfig[] = [
  { key: "mode", label: "Mode", type: "select", options: ["new", "existing"], required: true },
  { key: "cpu_cores", label: "CPU Cores", type: "number", min: 1, step: 1, required: true },
  { key: "ram_gb", label: "RAM (GB)", type: "number", min: 1, step: 1, required: true },
  { key: "expected_rps", label: "Expected RPS", type: "number", min: 1, step: 1, required: true },
  { key: "avg_response_ms", label: "Avg Response (ms)", type: "number", min: 1, step: 1, required: true },
];

const CALCULATORS: CalculatorConfig[] = [
  { key: "nginx", label: "NGINX", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "redis", label: "Redis", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "estimated_keys", label: "Estimated Keys", type: "number", min: 1, step: 1 }] },
  { key: "tomcat", label: "Tomcat", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "httpd", label: "Apache HTTPD", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "ohs", label: "Oracle HTTP Server", profiles: [{ key: "new", label: "New" }, { key: "new-fusion", label: "New Fusion" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "ihs", label: "IBM HTTP Server", profiles: [{ key: "new", label: "New" }, { key: "new-liberty", label: "New Liberty" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "iis", label: "IIS", profiles: [{ key: "new-core", label: "New Core" }, { key: "new-fx", label: "New Framework" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "os_type", label: "OS Type", type: "text", placeholder: "windows-server-2022" }] },
  { key: "podman", label: "Podman", profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1 }] },
  { key: "k8s", label: "Kubernetes", profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1 }] },
  { key: "os", label: "Linux OS", profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "workload_type", label: "Workload Type", type: "select", options: ["web", "database"] }] },
  { key: "postgresql", label: "PostgreSQL", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "connections", label: "Connections", type: "number", min: 50, step: 1 }] },
  { key: "mysql", label: "MySQL", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "connections", label: "Connections", type: "number", min: 50, step: 1 }] },
  { key: "mongodb", label: "MongoDB", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "connections", label: "Connections", type: "number", min: 50, step: 1 }] },
  { key: "haproxy", label: "HAProxy", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "connections", label: "Connections", type: "number", min: 50, step: 1 }] },
  { key: "docker", label: "Docker", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: COMMON_FIELDS },
  { key: "rabbitmq", label: "RabbitMQ", profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }], fields: [...COMMON_FIELDS, { key: "queues", label: "Queue Count", type: "number", min: 1, step: 1 }] },
];

export default function CalculatorPage() {
  const [calculator, setCalculator] = useState(CALCULATORS[0].key);
  const [profile, setProfile] = useState(CALCULATORS[0].profiles[0].key);
  const [values, setValues] = useState<Record<string, string | number | boolean>>({
    mode: "new",
    cpu_cores: 4,
    ram_gb: 16,
    expected_rps: 1000,
    avg_response_ms: 120,
  });
  const [loadingExample, setLoadingExample] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  const selected = useMemo(
    () => CALCULATORS.find((c) => c.key === calculator) ?? CALCULATORS[0],
    [calculator]
  );

  const setValue = (key: string, val: string | number | boolean) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  };

  const loadExample = async () => {
    setLoadingExample(true);
    setError("");
    try {
      const data = await getCalculatorExample(calculator, profile);
      setValues(data ?? {});
      setResult(null);
    } catch (e: any) {
      setError(e?.detail ?? e?.message ?? "Failed to load example.");
    } finally {
      setLoadingExample(false);
    }
  };

  const run = async () => {
    setLoadingRun(true);
    setError("");
    try {
      const payload: Record<string, unknown> = {};
      for (const f of selected.fields) {
        const raw = values[f.key];
        if (raw === undefined || raw === "") continue;
        if (f.type === "number") payload[f.key] = Number(raw);
        else if (f.type === "boolean") payload[f.key] = Boolean(raw);
        else payload[f.key] = raw;
      }
      if (!payload.mode) payload.mode = profile.includes("existing") ? "existing" : "new";
      const res = await runCalculator(calculator, payload);
      setResult(res);
    } catch (e: any) {
      const detail = Array.isArray(e?.detail)
        ? e.detail.map((x: any) => x?.msg ?? JSON.stringify(x)).join(", ")
        : e?.detail;
      setError(detail ?? e?.message ?? "Calculation failed.");
    } finally {
      setLoadingRun(false);
    }
  };

  const resultText = useMemo(() => {
    if (!result) return "Run calculation to see result";
    const lines: string[] = [];
    lines.push(`Calculator: ${result.calculator ?? calculator}`);
    lines.push(`Mode: ${result.mode ?? values.mode ?? "new"}`);
    if (result.summary) lines.push(`Summary: ${result.summary}`);
    if (typeof result.estimated_concurrency !== "undefined") {
      lines.push(`Estimated Concurrency: ${result.estimated_concurrency}`);
    }
    if (typeof result.workers !== "undefined") {
      lines.push(`Workers: ${result.workers}`);
    }
    if (typeof result.max_connections !== "undefined") {
      lines.push(`Max Connections: ${result.max_connections}`);
    }
    if (result.config_snippet) {
      lines.push("");
      lines.push("Recommended Config:");
      lines.push(String(result.config_snippet));
    }
    if (Array.isArray(result.major_params) && result.major_params.length > 0) {
      lines.push("");
      lines.push("Major Recommendations:");
      for (const p of result.major_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.medium_params) && result.medium_params.length > 0) {
      lines.push("");
      lines.push("Medium Recommendations:");
      for (const p of result.medium_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.minor_params) && result.minor_params.length > 0) {
      lines.push("");
      lines.push("Minor Recommendations:");
      for (const p of result.minor_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.audit_findings) && result.audit_findings.length > 0) {
      lines.push("");
      lines.push("Audit Findings:");
      for (const f of result.audit_findings) lines.push(`- ${f}`);
    }
    return lines.join("\n");
  }, [result, calculator, values.mode]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-300">
            <Calculator className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Infrastructure Calculator</h1>
            <p className="text-sm text-slate-400">Enter values in form fields and run instantly.</p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Calculator</p>
            <div className="space-y-2">
              {CALCULATORS.map((c) => (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => {
                    setCalculator(c.key);
                    setProfile(c.profiles[0].key);
                    setError("");
                    setResult(null);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${calculator === c.key ? "border-cyan-500/70 bg-cyan-500/10 text-cyan-100" : "border-slate-800 bg-slate-900 text-slate-200 hover:border-slate-700"}`}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </aside>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Profile</span>
                <select
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                >
                  {selected.profiles.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
                </select>
              </label>
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={loadExample}
                  disabled={loadingExample}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm text-slate-100 disabled:opacity-60"
                >
                  {loadingExample ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
                  Load Example
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {selected.fields.map((f) => (
                <label key={f.key} className="flex flex-col gap-1.5">
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{f.label}</span>
                  {f.type === "select" ? (
                    <select
                      value={(values[f.key] ?? "").toString()}
                      onChange={(e) => setValue(f.key, e.target.value)}
                      className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                    >
                      {(f.options ?? []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                    </select>
                  ) : f.type === "boolean" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(values[f.key])}
                      onChange={(e) => setValue(f.key, e.target.checked)}
                      className="h-5 w-5"
                    />
                  ) : (
                    <input
                      type={f.type === "number" ? "number" : "text"}
                      value={(values[f.key] ?? "").toString()}
                      placeholder={f.placeholder}
                      min={f.min}
                      max={f.max}
                      step={f.step}
                      onChange={(e) => setValue(f.key, f.type === "number" ? e.target.value : e.target.value)}
                      className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                    />
                  )}
                </label>
              ))}
            </div>

            <div className="mt-4 flex items-center gap-3">
              <button
                type="button"
                onClick={run}
                disabled={loadingRun}
                className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-cyan-600 px-5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {loadingRun ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run Calculator
              </button>
              {error ? <p className="text-sm text-rose-400">{error}</p> : null}
            </div>

            <div className="mt-5">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Result</p>
              <pre className="max-h-[460px] overflow-auto rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-100">
                {resultText}
              </pre>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
