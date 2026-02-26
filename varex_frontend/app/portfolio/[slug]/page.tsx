"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getProject } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function ProjectDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    getProject(slug)
      .then(setProject)
      .catch((err) => {
        setError(err?.response?.status === 404 ? "notfound" : "unknown");
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  if (error === "notfound") return (
    <div className="max-w-xl mx-auto text-center py-20 space-y-3">
      <p className="text-4xl">🗂</p>
      <h1 className="text-xl font-semibold">Project not found</h1>
      <p className="text-sm text-slate-400">This case study may have been moved or removed.</p>
      <Link href="/portfolio" className="inline-block text-xs text-sky-400 hover:text-sky-300 mt-2">
        ← Back to Portfolio
      </Link>
    </div>
  );

  if (!project) return null;

  const CATEGORY_COLORS: Record<string, string> = {
    devops: "bg-sky-500/20 text-sky-300",
    security: "bg-red-500/20 text-red-300",
    sap: "bg-amber-500/20 text-amber-300",
    architecture: "bg-purple-500/20 text-purple-300",
    ai_hiring: "bg-emerald-500/20 text-emerald-300",
  };

  return (
    <article className="max-w-3xl mx-auto space-y-8">

      {/* ── Breadcrumb ────────────────────────────────────────── */}
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/portfolio" className="hover:text-sky-300">Portfolio</Link>
        <span>/</span>
        <Link href={`/portfolio?category=${project.category || ''}`}
          className="hover:text-sky-300 capitalize">
          {project.category?.replace("_", " ") || "Uncategorized"}
        </Link>
        <span>/</span>
        <span className="text-slate-300 truncate max-w-[180px]">{project.title}</span>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────── */}
      <header className="space-y-3">
        <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide
          ${CATEGORY_COLORS[project.category || ""] ?? "bg-slate-700 text-slate-300"}`}>
          {project.category?.replace("_", " ") || "Uncategorized"}
        </span>
        {project.is_featured && (
          <span className="ml-2 inline-block rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] text-amber-300">
            ⭐ Featured
          </span>
        )}
        <h1 className="text-3xl font-bold leading-snug">{project.title}</h1>
        <p className="text-sm text-slate-300">{project.summary}</p>
        <p className="text-[11px] text-slate-500">
          Published {new Date(project.created_at).toLocaleDateString("en-IN", {
            day: "numeric", month: "long", year: "numeric"
          })}
        </p>
      </header>

      <hr className="border-slate-800" />

      {/* ── Architecture diagram (if available) ───────────────── */}
      {project.diagram_s3_key && (
        <div className="rounded-xl border border-slate-700 overflow-hidden">
          <img
            src={`https://your-s3-bucket.s3.ap-south-1.amazonaws.com/${project.diagram_s3_key}`}
            alt={`${project.title} architecture diagram`}
            className="w-full object-contain bg-slate-900"
          />
          <p className="px-3 py-2 text-[10px] text-slate-500 text-center">
            Architecture diagram — {project.title}
          </p>
        </div>
      )}

      {/* ── Description ───────────────────────────────────────── */}
      <section className="space-y-2">
        <h2 className="text-base font-semibold">Overview</h2>
        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
          {project.description}
        </p>
      </section>

      {/* ── Tech stack + Outcomes in 2 cols ───────────────────── */}
      <section className="grid gap-4 sm:grid-cols-2">
        {project.tech_stack && project.tech_stack.length > 0 && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="text-xs font-semibold text-slate-200 mb-3">🛠 Tech Stack</h2>
            <div className="flex flex-wrap gap-1.5">
              {project.tech_stack.map((tech) => (
                <span key={tech}
                  className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] text-sky-300">
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}

        {project.outcomes && project.outcomes.length > 0 && (
          <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/20 p-4">
            <h2 className="text-xs font-semibold text-slate-200 mb-3">✅ Outcomes & Impact</h2>
            <ul className="space-y-1.5">
              {project.outcomes.map((outcome) => (
                <li key={outcome} className="flex items-start gap-2 text-xs text-emerald-200">
                  <span className="mt-0.5 text-emerald-400 flex-shrink-0">✓</span>
                  {outcome}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* ── Links ─────────────────────────────────────────────── */}
      {(project.github_url || project.case_study_url) && (
        <div className="flex flex-wrap gap-3">
          {project.github_url && (
            <a href={project.github_url} target="_blank" rel="noopener"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700
                px-3 py-2 text-xs text-slate-200 hover:border-sky-500 hover:text-sky-300">
              ⬡ View on GitHub
            </a>
          )}
          {project.case_study_url && (
            <a href={project.case_study_url} target="_blank" rel="noopener"
              className="inline-flex items-center gap-1.5 rounded-md bg-sky-500
                px-3 py-2 text-xs font-semibold text-white hover:bg-sky-400">
              📄 Full Case Study
            </a>
          )}
        </div>
      )}

      {/* ── CTA ───────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-sky-700/40 bg-sky-950/30 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-sky-100">Want something like this built?</p>
          <p className="text-xs text-slate-300 mt-0.5">
            Book a free 30-min consultation with our architects.
          </p>
        </div>
        <Link href="/contact"
          className="flex-shrink-0 rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
          Book free consultation
        </Link>
      </div>

      {/* ── Footer nav ────────────────────────────────────────── */}
      <div className="border-t border-slate-800 pt-4">
        <Link href="/portfolio"
          className="text-xs text-slate-400 hover:text-sky-300">
          ← Back to Portfolio
        </Link>
      </div>

    </article>
  );
}
