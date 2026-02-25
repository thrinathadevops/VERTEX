// PATH: app/error.tsx
"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to monitoring service (Sentry etc.) in production
    console.error("Global error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-5 px-4">
      <p className="text-5xl">⚠️</p>
      <div className="space-y-1">
        <h1 className="text-xl font-bold text-slate-100">Something went wrong</h1>
        <p className="text-sm text-slate-400 max-w-sm">
          An unexpected error occurred. Our team has been notified.
          {error.digest && (
            <span className="block mt-1 text-[11px] text-slate-500">
              Error ID: {error.digest}
            </span>
          )}
        </p>
      </div>
      <div className="flex flex-wrap gap-3 justify-center">
        <button onClick={reset}
          className="rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-400 transition">
          Try again
        </button>
        <Link href="/"
          className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm text-slate-200 hover:border-sky-500/60 transition">
          Go home
        </Link>
      </div>
    </div>
  );
}
