"use client";
import { useEffect, useState } from "react";
import { listProjects } from "@/lib/api";
import type { Project, ProjectCategory } from "@/lib/types";

const CATEGORIES: { label: string; value: ProjectCategory | "all" }[] = [
  { label: "All", value: "all" },
  { label: "DevOps", value: "devops" },
  { label: "Security", value: "security" },
  { label: "SAP", value: "sap" },
  { label: "Architecture", value: "architecture" },
  { label: "AI Hiring", value: "ai_hiring" },
];

export default function PortfolioPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [active, setActive] = useState<ProjectCategory | "all">("all");

  useEffect(() => {
    listProjects(active === "all" ? undefined : active).then(setProjects);
  }, [active]);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold mb-1">Portfolio & Projects</h1>
        <p className="text-sm text-slate-300">Real-world implementations across DevSecOps, Security, SAP SD and AI hiring.</p>
      </header>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <button
            key={c.value}
            onClick={() => setActive(c.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium border ${active === c.value
                ? "bg-sky-500 border-sky-500 text-white"
                : "border-slate-700 text-slate-300 hover:border-sky-500"
              }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => (
          <article key={p.id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 hover:border-sky-600/70">
            <span className="inline-block rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300 mb-2">
              {p.category?.replace("_", " ") || "Uncategorized"}
            </span>
            <h2 className="text-sm font-semibold mb-1">{p.title}</h2>
            <p className="text-xs text-slate-300 mb-3 line-clamp-2">{p.summary}</p>
            {p.tech_stack && (
              <div className="flex flex-wrap gap-1 mb-3">
                {p.tech_stack.slice(0, 4).map((t) => (
                  <span key={t} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-sky-300">{t}</span>
                ))}
              </div>
            )}
            {p.outcomes && p.outcomes.length > 0 && (
              <p className="text-xs text-emerald-300">✓ {p.outcomes[0]}</p>
            )}
            {p.github_url && (
              <a href={p.github_url} target="_blank" rel="noopener"
                className="mt-2 inline-block text-[11px] text-sky-400 hover:text-sky-300">
                View on GitHub →
              </a>
            )}
          </article>
        ))}
        {projects.length === 0 && (
          <p className="text-xs text-slate-400 col-span-3">No projects found. Check back soon.</p>
        )}
      </div>
    </div>
  );
}
