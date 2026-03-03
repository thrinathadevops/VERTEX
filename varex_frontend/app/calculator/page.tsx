"use client";

import { useMemo, useState } from "react";
import { Calculator, Play, FileJson } from "lucide-react";
import { getCalculatorExample, runCalculator } from "@/lib/api";

type CalculatorOption = {
  key: string;
  label: string;
  examples: { key: string; label: string }[];
};

const CALCULATORS: CalculatorOption[] = [
  { key: "nginx", label: "NGINX", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "redis", label: "Redis", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "tomcat", label: "Tomcat", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "httpd", label: "Apache HTTPD", examples: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }] },
  { key: "ohs", label: "Oracle HTTP Server", examples: [{ key: "new", label: "New" }, { key: "new-fusion", label: "New Fusion" }, { key: "existing", label: "Existing" }] },
  { key: "ihs", label: "IBM HTTP Server", examples: [{ key: "new", label: "New" }, { key: "new-liberty", label: "New Liberty" }, { key: "existing", label: "Existing" }] },
  { key: "iis", label: "IIS", examples: [{ key: "new-core", label: "New Core" }, { key: "new-fx", label: "New Framework" }, { key: "existing", label: "Existing" }] },
  { key: "podman", label: "Podman", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
  { key: "k8s", label: "Kubernetes", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
  { key: "os", label: "Linux OS", examples: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }] },
];

export default function CalculatorPage() {
  const [calculator, setCalculator] = useState<string>(CALCULATORS[0].key);
  const [example, setExample] = useState<string>("new");
  const [payloadText, setPayloadText] = useState<string>('{\n  "mode": "new"\n}');
  const [resultText, setResultText] = useState<string>("");
  const [errorText, setErrorText] = useState<string>("");
  const [loadingExample, setLoadingExample] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);

  const selected = useMemo(
    () => CALCULATORS.find((item) => item.key === calculator) ?? CALCULATORS[0],
    [calculator]
  );

  const handleLoadExample = async () => {
    setLoadingExample(true);
    setErrorText("");
    try {
      const data = await getCalculatorExample(calculator, example);
      setPayloadText(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setErrorText(err?.detail ?? err?.message ?? "Failed to load example payload.");
    } finally {
      setLoadingExample(false);
    }
  };

  const handleRun = async () => {
    setLoadingRun(true);
    setErrorText("");
    setResultText("");
    try {
      const payload = JSON.parse(payloadText) as Record<string, unknown>;
      const result = await runCalculator(calculator, payload);
      setResultText(JSON.stringify(result, null, 2));
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

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:py-10">
      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5 sm:p-7">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-300">
            <Calculator className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white sm:text-2xl">Infrastructure Calculator</h1>
            <p className="text-sm text-slate-400">Integrated VAREX calculators inside the main application.</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Calculator</span>
            <select
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
              value={calculator}
              onChange={(e) => {
                const next = e.target.value;
                setCalculator(next);
                const firstExample = CALCULATORS.find((item) => item.key === next)?.examples[0]?.key ?? "new";
                setExample(firstExample);
              }}
            >
              {CALCULATORS.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Example Payload</span>
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

          <div className="flex items-end">
            <button
              type="button"
              onClick={handleLoadExample}
              disabled={loadingExample}
              className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm font-semibold text-slate-100 transition hover:border-cyan-400 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <FileJson className="h-4 w-4" />
              {loadingExample ? "Loading..." : "Load Example"}
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Request JSON</p>
            <textarea
              className="h-[420px] w-full resize-y rounded-xl border border-slate-800 bg-slate-900 p-3 font-mono text-xs text-slate-100 outline-none focus:border-cyan-400"
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              spellCheck={false}
            />
          </div>
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Response JSON</p>
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
            <Play className="h-4 w-4" />
            {loadingRun ? "Running..." : "Run Calculator"}
          </button>
          {errorText ? <p className="text-sm text-rose-400">{errorText}</p> : null}
        </div>
      </section>
    </main>
  );
}
