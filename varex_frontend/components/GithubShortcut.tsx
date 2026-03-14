"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

export default function GithubShortcut() {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label="VAREX GitHub"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-700 text-slate-400 transition-all duration-300 hover:border-sky-500/50 hover:bg-sky-500/10 hover:text-sky-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
          <path d="M12 .3a12 12 0 0 0-3.79 23.4c.6.1.83-.26.83-.57v-2.18c-3.34.72-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.64 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .31.22.68.83.56A12 12 0 0 0 12 .3z" />
        </svg>
      </button>

      <div
        className={`pointer-events-none absolute bottom-14 left-0 z-30 w-[280px] rounded-2xl border border-slate-700/80 bg-slate-950/95 p-4 text-left shadow-2xl shadow-black/40 backdrop-blur-md transition-all duration-200 ${
          open ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
        }`}
        role="dialog"
        aria-hidden={!open}
      >
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-sky-400">
          VAREX GitHub
        </p>
        <p className="mt-2 text-sm font-semibold text-white">
          Engineering knowledge, pipelines, and DevOps delivery patterns.
        </p>
        <p className="mt-2 text-xs leading-relaxed text-slate-400">
          This is the official VAREX GitHub space for DevOps repositories, CI/CD pipelines,
          infrastructure automation, deployment references, and production-oriented engineering assets.
        </p>
        <Link
          href="https://github.com/varextech/"
          target="_blank"
          rel="noopener noreferrer"
          className="pointer-events-auto mt-3 inline-flex items-center rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-xs font-semibold text-sky-300 transition-colors hover:border-sky-400/50 hover:text-sky-200"
        >
          Open official GitHub
        </Link>
      </div>
    </div>
  );
}
