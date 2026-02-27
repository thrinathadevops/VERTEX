"use client";

import { useEffect, useRef, useState } from "react";

type StatusResponse = {
  ok: boolean;
  launchUrl?: string;
  message?: string;
};

export default function AIInterviewLauncherPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const launchedRef = useRef(false);

  const launchAIInterview = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/ai-interview/status", { cache: "no-store" });
      const payload = (await res.json()) as StatusResponse;

      if (!res.ok || !payload.ok || !payload.launchUrl) {
        setError(payload.message || "AI Interview application is not available right now.");
        return;
      }

      window.location.assign(payload.launchUrl);
    } catch {
      setError("Could not connect to AI Interview application. Please retry in a moment.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (launchedRef.current) return;
    launchedRef.current = true;
    launchAIInterview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="max-w-3xl mx-auto py-20 px-4">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">AI Interview Application</h1>
        <p className="text-slate-300 leading-relaxed mb-6">
          You are about to open the standalone AI Interview app running as a separate platform.
          We verify service availability first to prevent broken redirects.
        </p>
        <button
          type="button"
          onClick={launchAIInterview}
          disabled={loading}
          className="inline-flex items-center rounded-lg bg-sky-500 hover:bg-sky-400 disabled:opacity-70 px-5 py-3 text-sm font-semibold text-white transition-colors"
        >
          {loading ? "Checking AI App..." : "Retry Opening AI Interview App"}
        </button>
        {error && (
          <div className="mt-5 rounded-lg border border-red-500/40 bg-red-900/20 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
