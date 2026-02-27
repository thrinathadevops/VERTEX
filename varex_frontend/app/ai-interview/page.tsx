"use client";

import { useEffect, useState } from "react";
import { Bot, AlertTriangle, ArrowLeft, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AIInterviewRedirect() {
  const [status, setStatus] = useState<"checking" | "up" | "down">("checking");
  const router = useRouter();

  useEffect(() => {
    // Determine the AI app URL dynamically based on current host (assumes AI app runs on port 3010)
    const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
    const aiAppUrl = `http://${host}:3010`;

    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 4000); // 4 sec timeout

        // Ping the health endpoint exposed by Nginx in the AI Interview app
        const res = await fetch(`${aiAppUrl}/health`, {
          signal: controller.signal,
          method: "GET",
          headers: {
            Accept: "application/json"
          }
        });
        clearTimeout(timeoutId);

        if (res.ok) {
          const data = await res.json();
          if (data.status === "ok") {
            setStatus("up");
            // Redirect to the actual AI application frontend
            window.location.href = aiAppUrl;
            return;
          }
        }

        throw new Error("Service not healthy");
      } catch (error) {
        console.error("AI Interview health check failed:", error);
        setStatus("down");
      }
    };

    checkHealth();
  }, []);

  if (status === "checking" || status === "up") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <Bot className="w-16 h-16 text-cyan-400 animate-pulse mb-6" />
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
          {status === "checking" ? "Connecting to AI Core..." : "Redirecting to AI Interview Workspace..."}
        </h1>
        <p className="text-slate-400 mb-8 max-w-md leading-relaxed">
          {status === "checking"
            ? "We are verifying the isolated AI infrastructure and preparing your secure assessment environment."
            : "Connection established. Transferring you securely."}
        </p>
        <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    );
  }

  // Error state
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 animate-in fade-in duration-500">
      <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
        <AlertTriangle className="w-10 h-10 text-red-500" />
      </div>
      <h1 className="text-2xl md:text-3xl font-bold text-white mb-3">
        AI Interview Infrastructure Offline
      </h1>
      <p className="text-slate-400 max-w-lg mb-8 leading-relaxed">
        The dedicated AI evaluation environment is currently unreachable. The backend systems might be redeploying via CI/CD, experiencing heavy load, or undergoing scheduled maintenance.
      </p>

      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-5 mb-8 text-left max-w-md w-full shadow-inner">
        <h3 className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          Diagnostic Details
        </h3>
        <ul className="text-xs text-slate-400 space-y-2 font-mono">
          <li className="flex justify-between">
            <span>Target Subsystem:</span>
            <span className="text-cyan-400">AI Engine</span>
          </li>
          <li className="flex justify-between">
            <span>Expected Port:</span>
            <span className="text-amber-400">3010</span>
          </li>
          <li className="flex justify-between">
            <span>Endpoint:</span>
            <span>/health</span>
          </li>
          <li className="flex justify-between pt-2 border-t border-slate-800/60">
            <span>Last Status:</span>
            <span className="text-red-400 font-semibold">Connection Refused / Timeout</span>
          </li>
        </ul>
      </div>

      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors border border-slate-700 hover:border-slate-600 shadow-lg"
      >
        <ArrowLeft className="w-4 h-4" />
        Return to Dashboard
      </button>
    </div>
  );
}
