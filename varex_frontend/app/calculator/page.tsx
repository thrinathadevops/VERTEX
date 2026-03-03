"use client";

import { useMemo, useState } from "react";
import { Calculator, Play, FileJson, CheckCircle2, Loader2, Copy, RotateCcw } from "lucide-react";
import { getCalculatorExample, runCalculator } from "@/lib/api";

type CalculatorOption = {
  key: string;
  label: string;
  domain: string;
  summary: string;
  examples: { key: string; label: string }[];
};

const CALCULATORS: CalculatorOption[] = [
  { key: "nginx", label: "NGINX", domain: "Web Server", summary: "High-throughput reverse proxy and edge tuning.", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "redis", label: "Redis", domain: "Data Layer", summary: "Memory, eviction, durability, and latency safety.", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "tomcat", label: "Tomcat", domain: "Java Runtime", summary: "Thread pools, heap, GC, and connector sizing.", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "httpd", label: "Apache HTTPD", domain: "Web Server", summary: "MPM, KeepAlive, and worker capacity optimization.", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "ohs", label: "Oracle HTTP Server", domain: "Middleware", summary: "OHS and Fusion middleware-safe hardening profiles.", examples: [{ key: "new", label: "New" }, { key: "new-fusion", label: "New Fusion" }, { key: "existing", label: "Existing" }] },
  { key: "ihs", label: "IBM HTTP Server", domain: "Middleware", summary: "IHS web and Liberty application gateway tuning.", examples: [{ key: "new", label: "New" }, { key: "new-liberty", label: "New Liberty" }, { key: "existing", label: "Existing" }] },
  { key: "iis", label: "IIS", domain: "Windows", summary: "App pool, queue, memory, and request pipeline settings.", examples: [{ key: "new-core", label: "New Core" }, { key: "new-fx", label: "New Framework" }, { key: "existing", label: "Existing" }] },
  { key: "podman", label: "Podman", domain: "Containers", summary: "Container limits, files, and host-level runtime tuning.", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
  { key: "k8s", label: "Kubernetes", domain: "Orchestration", summary: "Pod resources, HPA/PDB, spread, and network policies.", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
  { key: "os", label: "Linux OS", domain: "Kernel", summary: "Kernel, VM, network, and file descriptor tuning.", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
];

export default function CalculatorPage() {
  const [calculator, setCalculator] = useState<string>(CALCULATORS[0].key);
  const [example, setExample] = useState<string>("new");
  const [payloadText, setPayloadText] = useState<string>('{\n  "mode": "new"\n}');
  const [resultText, setResultText] = useState<string>("");
  const [errorText, setErrorText] = useState<string>("");
  const [okText, setOkText] = useState<string>("");
  const [loadingExample, setLoadingExample] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);

  const selected = useMemo(
    () => CALCULATORS.find((item) => item.key === calculator) ?? CALCULATORS[0],
    [calculator]
  );

  const endpointPath = `/api/v1/calculators/${calculator}/calculate`;

  const setDefaultPayload = () => setPayloadText('{\n  "mode": "new"\n}');

  const handleLoadExample = async () => {
    setLoadingExample(true);
    setErrorText("");
    setOkText("");
    try {
      const data = await getCalculatorExample(calculator, example);
      setPayloadText(JSON.stringify(data, null, 2));
      setOkText("Example payload loaded.");
    } catch (err: any) {
      setErrorText(err?.detail ?? err?.message ?? "Failed to load example payload.");
    } finally {
      setLoadingExample(false);
    }
  };

  const handleRun = async () => {
    setLoadingRun(true);
    setErrorText("");
    setOkText("");
    setResultText("");
    try {
      const payload = JSON.parse(payloadText) as Record<string, unknown>;
      const result = await runCalculator(calculator, payload);
      setResultText(JSON.stringify(result, null, 2));
      setOkText("Calculation completed successfully.");
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setErrorText("Payload is not valid JSON.");
      } else {
        setErrorText(err?.detail ?? err?.message ?? "Calculator request failed.");
      }
    } finally {
      setLoadingRun(false);
    }
  };

  const handleCopyResult = async () => {
    if (!resultText) return;
    try {
      await navigator.clipboard.writeText(resultText);
      setOkText("Result copied to clipboard.");
      setErrorText("");
    } catch {
      setErrorText("Unable to copy result.");
    }
  };

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:py-8">
      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4 sm:p-6">
        <div className="mb-4 flex flex-col gap-3 border-b border-slate-800 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-300">
              <Calculator className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white sm:text-2xl">VAREX Infrastructure Calculator</h1>
              <p className="text-sm text-slate-400">Enterprise tuning console integrated in the main platform.</p>
            </div>
          </div>
          <div className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300">
            Endpoint: <span className="ml-2 font-mono text-cyan-300">{endpointPath}</span>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Calculator Catalog</p>
            <div className="space-y-2">
              {CALCULATORS.map((item) => {
                const active = item.key === calculator;
                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => {
                      setCalculator(item.key);
                      setExample(item.examples[0]?.key ?? "new");
                      setErrorText("");
                      setOkText("");
                    }}
                    className={`w-full cursor-pointer rounded-lg border px-3 py-2 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-400 ${active ? "border-cyan-500/70 bg-cyan-500/10" : "border-slate-800 bg-slate-900 hover:border-slate-700"}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-sm font-semibold ${active ? "text-cyan-200" : "text-slate-100"}`}>{item.label}</span>
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">{item.domain}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">{item.summary}</p>
                  </button>
                );
              })}
            </div>
          </aside>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 sm:p-4">
            <div className="mb-3 rounded-lg border border-slate-800 bg-slate-900 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-white">{selected.label}</p>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">{selected.domain}</span>
              </div>
              <p className="mt-1 text-xs text-slate-400">{selected.summary}</p>
            </div>

            <div className="mb-4 grid gap-3 sm:grid-cols-[minmax(0,220px)_1fr]">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Profile</span>
                <select
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
                  value={example}
                  onChange={(e) => setExample(e.target.value)}
                >
                  {selected.examples.map((item) => (
                    <option key={item.key} value={item.key}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>

              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={handleLoadExample}
                  disabled={loadingExample}
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm font-semibold text-slate-100 transition hover:border-cyan-400 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loadingExample ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileJson className="h-4 w-4" />}
                  {loadingExample ? "Loading..." : "Load Example"}
                </button>
                <button
                  type="button"
                  onClick={setDefaultPayload}
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm font-semibold text-slate-100 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </button>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Request JSON</p>
                <textarea
                  className="h-[420px] w-full resize-y rounded-xl border border-slate-800 bg-slate-900 p-3 font-mono text-xs text-slate-100 outline-none focus:border-cyan-400"
                  value={payloadText}
                  onChange={(e) => setPayloadText(e.target.value)}
                  spellCheck={false}
                  aria-label="Request JSON payload"
                />
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Response JSON</p>
                  <button
                    type="button"
                    onClick={handleCopyResult}
                    disabled={!resultText}
                    className="inline-flex min-h-8 items-center gap-1 rounded-md border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Copy
                  </button>
                </div>
                <pre className="h-[420px] overflow-auto rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-100">
                  {resultText || "Run the calculator to see output here."}
                </pre>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                type="button"
                onClick={handleRun}
                disabled={loadingRun}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-cyan-600 px-5 text-sm font-semibold text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingRun ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {loadingRun ? "Running..." : "Run Calculator"}
              </button>
              {okText ? (
                <p className="inline-flex items-center gap-1.5 text-sm text-emerald-400" role="status">
                  <CheckCircle2 className="h-4 w-4" />
                  {okText}
                </p>
              ) : null}
              {errorText ? (
                <p className="text-sm text-rose-400" role="alert">
                  {errorText}
                </p>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
