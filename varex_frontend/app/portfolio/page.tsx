"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Github, Globe, Sparkles } from "lucide-react";
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

const CATEGORY_ACCENTS: Record<string, string> = {
  devops: "from-sky-400/20 via-cyan-400/10 to-transparent text-sky-200 border-sky-400/20",
  security: "from-rose-400/20 via-orange-400/10 to-transparent text-rose-200 border-rose-400/20",
  sap: "from-amber-400/20 via-yellow-300/10 to-transparent text-amber-100 border-amber-400/20",
  architecture: "from-violet-400/20 via-indigo-400/10 to-transparent text-violet-100 border-violet-400/20",
  ai_hiring: "from-emerald-400/20 via-lime-300/10 to-transparent text-emerald-100 border-emerald-400/20",
};

export default function PortfolioPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [active, setActive] = useState<ProjectCategory | "all">("all");

  useEffect(() => {
    listProjects(active === "all" ? undefined : active).then(setProjects);
  }, [active]);

  const featuredProjects = useMemo(
    () => projects.filter((project) => project.is_featured).slice(0, 2),
    [projects]
  );

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/6 bg-[linear-gradient(135deg,rgba(5,14,15,0.98),rgba(5,12,21,0.94),rgba(7,16,14,0.96))] px-6 py-10 md:px-10 md:py-14">
        <div className="absolute inset-y-0 left-0 w-1/2 bg-[radial-gradient(circle_at_left_top,rgba(16,185,129,0.14),transparent_72%)]" />
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_right_top,rgba(56,189,248,0.12),transparent_72%)]" />
        <div className="relative grid gap-10 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-5">
            <span className="terminal-label">Portfolio Command Layer</span>
            <div className="space-y-4">
              <h1 className="max-w-4xl text-4xl font-black tracking-tight text-white md:text-6xl">
                Case studies that show architecture, execution, and delivery outcomes.
              </h1>
              <p className="max-w-2xl text-base text-slate-300 md:text-lg">
                Every project here is manually curated and published. GitHub is proof when useful, but the portfolio stays focused on business impact, engineering clarity, and enterprise trust.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { label: "Publishing model", value: "Manual admin control" },
                { label: "Project style", value: "Case-study first" },
                { label: "Proof layer", value: "GitHub icon only" },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-500">{item.label}</p>
                  <p className="mt-2 text-sm font-semibold text-slate-100">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel rounded-[1.8rem] p-5">
            <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-200/70">Featured Delivery Tracks</p>
            <div className="mt-4 space-y-3">
              {featuredProjects.length > 0 ? featuredProjects.map((project) => (
                <Link
                  key={project.id}
                  href={`/portfolio/${project.slug}`}
                  className="group block rounded-2xl border border-white/6 bg-white/[0.04] p-4 transition-all hover:border-emerald-300/20 hover:bg-white/[0.06]"
                >
                  <div className="mb-3 flex items-center justify-between gap-4">
                    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100">
                      <Sparkles className="h-3.5 w-3.5" />
                      Featured
                    </span>
                    <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{project.project_type?.replace("_", " ") || "case study"}</span>
                  </div>
                  <h2 className="text-lg font-bold text-white">{project.title}</h2>
                  <p className="mt-2 text-sm text-slate-300">{project.summary}</p>
                  {project.outcomes?.[0] && (
                    <p className="mt-3 text-xs font-medium text-emerald-200">Outcome: {project.outcomes[0]}</p>
                  )}
                </Link>
              )) : (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] p-5 text-sm text-slate-400">
                  Featured case studies will appear here once published.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((category) => (
            <button
              key={category.value}
              onClick={() => setActive(category.value)}
              className={`rounded-full border px-4 py-2 text-xs font-semibold tracking-wide transition-all ${active === category.value
                ? "border-sky-400/40 bg-sky-400/15 text-sky-100"
                : "border-white/8 bg-white/[0.03] text-slate-300 hover:border-emerald-400/20 hover:text-white"
                }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => {
            const accent = CATEGORY_ACCENTS[project.category] || "from-slate-400/20 via-white/5 to-transparent text-slate-200 border-white/10";
            return (
              <article
                key={project.id}
                className="group relative overflow-hidden rounded-[1.6rem] border border-white/6 bg-[linear-gradient(180deg,rgba(7,14,18,0.94),rgba(4,8,12,0.98))] p-5 transition-all duration-300 hover:-translate-y-1 hover:border-emerald-300/18 hover:shadow-[0_24px_60px_rgba(0,0,0,0.28)]"
              >
                <div className={`absolute inset-x-0 top-0 h-28 bg-gradient-to-br ${accent} opacity-80`} />
                <div className="relative space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="inline-block rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-200">
                        {project.category.replace("_", " ")}
                      </span>
                      <h2 className="mt-3 text-xl font-bold text-white">{project.title}</h2>
                    </div>
                    <div className="flex items-center gap-2">
                      {project.github_url && (
                        <a
                          href={project.github_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`${project.title} GitHub`}
                          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] text-slate-200 transition-all hover:border-sky-400/30 hover:text-sky-200"
                        >
                          <Github className="h-4.5 w-4.5" />
                        </a>
                      )}
                      {project.demo_url && (
                        <a
                          href={project.demo_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`${project.title} demo`}
                          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] text-slate-200 transition-all hover:border-emerald-400/30 hover:text-emerald-200"
                        >
                          <Globe className="h-4.5 w-4.5" />
                        </a>
                      )}
                    </div>
                  </div>

                  {project.hero_image_url ? (
                    <div className="overflow-hidden rounded-[1.35rem] border border-white/8 bg-slate-950/40">
                      <img
                        src={project.hero_image_url}
                        alt={project.title}
                        className="h-52 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                      />
                    </div>
                  ) : (
                    <div className="rounded-[1.35rem] border border-dashed border-white/10 bg-white/[0.03] p-5">
                      <div className="grid gap-3 sm:grid-cols-2">
                        {(project.tech_stack || []).slice(0, 4).map((tech) => (
                          <div key={tech} className="rounded-xl border border-white/6 bg-slate-950/45 px-3 py-3 text-xs text-slate-200">
                            {tech}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <p className="text-sm leading-relaxed text-slate-300">{project.summary}</p>

                  <div className="flex flex-wrap gap-2">
                    {(project.tech_stack || []).slice(0, 5).map((tech) => (
                      <span key={tech} className="rounded-full border border-sky-400/12 bg-sky-400/8 px-3 py-1 text-[11px] text-sky-100">
                        {tech}
                      </span>
                    ))}
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/6 bg-white/[0.03] p-4">
                      <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Primary outcome</p>
                      <p className="mt-2 text-sm font-medium text-emerald-100">{project.outcomes?.[0] || "Outcome details can be published here."}</p>
                    </div>
                    <div className="rounded-2xl border border-white/6 bg-white/[0.03] p-4">
                      <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Project type</p>
                      <p className="mt-2 text-sm font-medium capitalize text-slate-100">{project.project_type?.replace("_", " ") || "Case study"}</p>
                    </div>
                  </div>

                  <Link
                    href={`/portfolio/${project.slug}`}
                    className="inline-flex items-center gap-2 text-sm font-semibold text-sky-200 transition-all hover:text-white"
                  >
                    View Case Study
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Link>
                </div>
              </article>
            );
          })}

          {projects.length === 0 && (
            <div className="col-span-full rounded-[1.6rem] border border-dashed border-white/10 bg-white/[0.03] p-8 text-center text-sm text-slate-400">
              No published projects found for this category yet.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
