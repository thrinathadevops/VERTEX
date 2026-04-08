"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Github, Globe } from "lucide-react";
import { getProject } from "@/lib/api";
import type { Project } from "@/lib/types";

const CATEGORY_COLORS: Record<string, string> = {
  devops: "bg-sky-500/18 text-sky-100 border-sky-400/18",
  security: "bg-rose-500/18 text-rose-100 border-rose-400/18",
  sap: "bg-amber-500/18 text-amber-100 border-amber-400/18",
  architecture: "bg-violet-500/18 text-violet-100 border-violet-400/18",
  ai_hiring: "bg-emerald-500/18 text-emerald-100 border-emerald-400/18",
};

function CaseStudySection({ title, body }: { title: string; body?: string }) {
  if (!body) return null;
  return (
    <section className="rounded-[1.6rem] border border-white/6 bg-[linear-gradient(180deg,rgba(8,14,20,0.92),rgba(5,10,14,0.98))] p-6">
      <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{title}</p>
      <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-300">{body}</p>
    </section>
  );
}

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

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-7 w-7 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error === "notfound") {
    return (
      <div className="mx-auto max-w-xl py-20 text-center">
        <h1 className="text-2xl font-bold text-white">Project not found</h1>
        <p className="mt-3 text-sm text-slate-400">This case study may have been moved or unpublished.</p>
        <Link href="/portfolio" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-sky-300 hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back to Portfolio
        </Link>
      </div>
    );
  }

  if (!project) return null;

  const stats = [
    project.client_name ? { label: "Client", value: project.client_name } : null,
    project.duration ? { label: "Duration", value: project.duration } : null,
    project.team_size ? { label: "Team Size", value: `${project.team_size}` } : null,
    project.role_played ? { label: "Role", value: project.role_played } : null,
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <article className="space-y-8">
      <nav className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
        <Link href="/portfolio" className="hover:text-sky-300">Portfolio</Link>
        <span>/</span>
        <span className="capitalize">{project.category.replace("_", " ")}</span>
        <span>/</span>
        <span className="truncate text-slate-300">{project.title}</span>
      </nav>

      <header className="relative overflow-hidden rounded-[2rem] border border-white/6 bg-[linear-gradient(135deg,rgba(6,14,18,0.98),rgba(5,12,22,0.96),rgba(7,17,15,0.96))]">
        <div className="absolute inset-y-0 left-0 w-1/2 bg-[radial-gradient(circle_at_left_top,rgba(16,185,129,0.16),transparent_72%)]" />
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_right_top,rgba(56,189,248,0.14),transparent_74%)]" />
        <div className="relative grid gap-8 p-6 md:p-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${CATEGORY_COLORS[project.category] || "border-white/10 bg-white/[0.05] text-slate-200"}`}>
                {project.category.replace("_", " ")}
              </span>
              {project.is_featured && (
                <span className="inline-flex rounded-full border border-amber-400/20 bg-amber-400/12 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-100">
                  Featured
                </span>
              )}
              <span className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-300">
                {project.project_type?.replace("_", " ") || "case study"}
              </span>
            </div>

            <div className="space-y-3">
              <h1 className="max-w-3xl text-4xl font-black tracking-tight text-white md:text-5xl">{project.title}</h1>
              <p className="max-w-2xl text-base leading-7 text-slate-300">{project.summary}</p>
            </div>

            <div className="flex flex-wrap gap-3">
              {project.github_url && (
                <a
                  href={project.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-slate-100 transition-all hover:border-sky-400/25 hover:text-white"
                >
                  <Github className="h-4 w-4" />
                  GitHub
                </a>
              )}
              {project.demo_url && (
                <a
                  href={project.demo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-xl bg-[linear-gradient(135deg,#0891b2,#0ea5e9)] px-4 py-2.5 text-sm font-semibold text-white transition-all hover:brightness-110"
                >
                  <Globe className="h-4 w-4" />
                  Live Demo
                </a>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {stats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{stat.label}</p>
                  <p className="mt-2 text-sm font-semibold text-slate-100">{stat.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            {project.hero_image_url ? (
              <div className="overflow-hidden rounded-[1.7rem] border border-white/10 bg-slate-950/50">
                <img src={project.hero_image_url} alt={project.title} className="h-[320px] w-full object-cover" />
              </div>
            ) : (
              <div className="rounded-[1.7rem] border border-dashed border-white/10 bg-white/[0.03] p-6">
                <p className="text-[11px] uppercase tracking-[0.22em] text-emerald-200/70">Architecture Snapshot</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {(project.tech_stack || []).slice(0, 6).map((tech) => (
                    <div key={tech} className="rounded-xl border border-white/6 bg-slate-950/40 px-3 py-3 text-sm text-slate-200">
                      {tech}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {project.outcomes?.length ? (
              <div className="rounded-[1.5rem] border border-emerald-400/12 bg-emerald-400/6 p-5">
                <p className="text-[11px] uppercase tracking-[0.22em] text-emerald-200/80">Outcomes</p>
                <ul className="mt-4 space-y-2">
                  {project.outcomes.slice(0, 4).map((outcome) => (
                    <li key={outcome} className="text-sm text-emerald-50">• {outcome}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[1.6rem] border border-white/6 bg-[linear-gradient(180deg,rgba(8,14,20,0.92),rgba(5,10,14,0.98))] p-6">
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Overview</p>
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-300">{project.description}</p>
        </div>

        <div className="space-y-6">
          {project.tech_stack?.length ? (
            <div className="rounded-[1.6rem] border border-white/6 bg-[linear-gradient(180deg,rgba(8,14,20,0.92),rgba(5,10,14,0.98))] p-6">
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Tech Stack</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {project.tech_stack.map((tech) => (
                  <span key={tech} className="rounded-full border border-sky-400/12 bg-sky-400/8 px-3 py-1 text-xs text-sky-100">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {project.screenshots?.length ? (
            <div className="rounded-[1.6rem] border border-white/6 bg-[linear-gradient(180deg,rgba(8,14,20,0.92),rgba(5,10,14,0.98))] p-6">
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Screenshots</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {project.screenshots.slice(0, 4).map((shot, index) => (
                  <div key={`${shot}-${index}`} className="overflow-hidden rounded-2xl border border-white/8 bg-slate-950/45">
                    <img src={shot} alt={`${project.title} screenshot ${index + 1}`} className="h-40 w-full object-cover" />
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <CaseStudySection title="Problem Statement" body={project.case_study_content?.problem_statement} />
        <CaseStudySection title="Solution Approach" body={project.case_study_content?.solution_approach} />
        <CaseStudySection title="Architecture Overview" body={project.case_study_content?.architecture_overview} />
        <CaseStudySection title="Security Considerations" body={project.case_study_content?.security_considerations} />
        <CaseStudySection title="Deployment Flow" body={project.case_study_content?.deployment_flow} />
        <CaseStudySection title="Results" body={project.case_study_content?.results} />
      </div>

      <CaseStudySection title="Lessons Learned" body={project.case_study_content?.lessons_learned} />

      <section className="rounded-[1.8rem] border border-sky-400/14 bg-[linear-gradient(135deg,rgba(8,21,39,0.92),rgba(6,16,28,0.96))] p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-lg font-semibold text-white">Need a similar delivery track for your business?</p>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              VAREX can design, harden, and deliver architecture like this with the same case-study discipline shown here.
            </p>
          </div>
          <Link href="/contact" className="inline-flex items-center gap-2 rounded-xl bg-[linear-gradient(135deg,#0891b2,#0ea5e9)] px-4 py-2.5 text-sm font-semibold text-white hover:brightness-110">
            Book Free Consultation
          </Link>
        </div>
      </section>

      <div className="border-t border-white/8 pt-5">
        <Link href="/portfolio" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-300 hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back to Portfolio
        </Link>
      </div>
    </article>
  );
}
