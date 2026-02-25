"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getContentBySlug } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";
import type { ContentItem } from "@/lib/types";

export default function LearningDetailPage() {
  const { slug }  = useParams<{ slug: string }>();
  const user      = getUserFromCookies();

  const [content, setContent] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    getContentBySlug(slug)
      .then(setContent)
      .catch((err) => {
        const status = err?.response?.status;
        if (status === 403)      setError("premium");
        else if (status === 404) setError("notfound");
        else                     setError("unknown");
      })
      .finally(() => setLoading(false));
  }, [slug]);

  // ── Loading ───────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  // ── 404 ───────────────────────────────────────────────────────
  if (error === "notfound") return (
    <div className="max-w-xl mx-auto text-center py-20 space-y-3">
      <p className="text-4xl">📭</p>
      <h1 className="text-xl font-semibold">Content not found</h1>
      <p className="text-sm text-slate-400">
        This learning module may have been moved or removed.
      </p>
      <Link href="/learnings"
        className="inline-block text-xs text-sky-400 hover:text-sky-300 mt-2">
        ← Back to Learnings
      </Link>
    </div>
  );

  // ── Premium gate ──────────────────────────────────────────────
  if (error === "premium") return (
    <div className="max-w-xl mx-auto py-20 space-y-5">
      <div className="rounded-2xl border border-amber-700/40 bg-amber-950/20 p-6 text-center space-y-4">
        <p className="text-4xl">🔒</p>
        <h1 className="text-xl font-semibold text-amber-100">Premium content</h1>
        <p className="text-sm text-slate-300">
          This learning module is available to <strong>Premium</strong> and{" "}
          <strong>Enterprise</strong> subscribers.
        </p>
        <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-3 text-left text-xs text-slate-300 space-y-1.5">
          <p className="font-medium text-slate-200 mb-2">Premium includes:</p>
          {[
            "Advanced DevSecOps courses",
            "Architecture deep dives",
            "Workshop recordings",
            "Downloadable templates & cheat sheets",
            "Interview prep content",
          ].map((f) => (
            <p key={f} className="flex items-center gap-2">
              <span className="text-emerald-400">✓</span> {f}
            </p>
          ))}
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link href="/pricing"
            className="rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
            Upgrade to Premium
          </Link>
          {!user && (
            <Link href="/login"
              className="rounded-md border border-slate-600 px-4 py-2 text-xs text-slate-200 hover:border-sky-500">
              Sign in
            </Link>
          )}
        </div>
      </div>
      <div className="text-center">
        <Link href="/learnings" className="text-xs text-slate-400 hover:text-sky-300">
          ← Back to Learnings
        </Link>
      </div>
    </div>
  );

  if (!content) return null;

  const readingMins = Math.ceil((content.body?.split(" ").length ?? 0) / 200);

  const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
    devops:       { label: "DevOps",       color: "bg-sky-500/20 text-sky-300",     icon: "⚙️" },
    security:     { label: "Security",     color: "bg-red-500/20 text-red-300",     icon: "🛡" },
    sap:          { label: "SAP SD",       color: "bg-amber-500/20 text-amber-300", icon: "📦" },
    architecture: { label: "Architecture", color: "bg-purple-500/20 text-purple-300", icon: "🏗" },
    ai_hiring:    { label: "AI Hiring",    color: "bg-emerald-500/20 text-emerald-300", icon: "🤖" },
  };

  const cat = content.category ?? "devops";
  const meta = CATEGORY_META[cat] ?? { label: cat, color: "bg-slate-700 text-slate-300", icon: "📄" };

  return (
    <div className="max-w-2xl mx-auto space-y-6">

      {/* ── Breadcrumb ──────────────────────────────────────────── */}
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/learnings" className="hover:text-sky-300">Learnings</Link>
        <span>/</span>
        <span className="text-slate-300 capitalize">{meta.label}</span>
        <span>/</span>
        <span className="text-slate-300 truncate max-w-[160px]">{content.title}</span>
      </nav>

      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5
            text-[10px] font-medium uppercase tracking-wide ${meta.color}`}>
            {meta.icon} {meta.label}
          </span>
          {content.access_level === "premium" && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] text-amber-300">
              ⭐ Premium
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold leading-snug">{content.title}</h1>
        <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
          <span>📅 {new Date(content.created_at).toLocaleDateString("en-IN", {
            day: "numeric", month: "long", year: "numeric"
          })}</span>
          <span>⏱ {readingMins} min read</span>
          {user && (
            <span className="capitalize text-sky-400">
              👤 {user.role.replace("_", " ")}
            </span>
          )}
        </div>
      </header>

      <hr className="border-slate-800" />

      {/* ── Content body ────────────────────────────────────────── */}
      <section
        className="prose prose-invert prose-sm max-w-none
          prose-headings:font-semibold prose-headings:text-slate-100
          prose-h2:text-lg prose-h3:text-base
          prose-p:text-slate-300 prose-p:leading-relaxed
          prose-a:text-sky-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-slate-100
          prose-code:bg-slate-800 prose-code:px-1 prose-code:rounded prose-code:text-sky-200
          prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-700 prose-pre:rounded-xl
          prose-blockquote:border-l-sky-500 prose-blockquote:text-slate-300 prose-blockquote:bg-slate-900/50 prose-blockquote:rounded-r-lg prose-blockquote:py-1
          prose-ul:text-slate-300 prose-ol:text-slate-300 prose-li:marker:text-sky-400
          prose-img:rounded-xl prose-img:border prose-img:border-slate-700
          prose-hr:border-slate-700"
        dangerouslySetInnerHTML={{ __html: content.body }}
      />

      {/* ── Bottom CTA strip ────────────────────────────────────── */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Want hands-on training?</p>
          <p className="text-xs text-slate-400 mt-0.5">
            Explore our live workshops or book a 1:1 consultation.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link href="/workshops"
            className="rounded-md border border-slate-600 px-3 py-2 text-xs
              text-slate-200 hover:border-sky-500 hover:text-sky-300">
            View workshops
          </Link>
          <Link href="/contact"
            className="rounded-md bg-sky-500 px-3 py-2 text-xs
              font-semibold text-white hover:bg-sky-400">
            Book consultation
          </Link>
        </div>
      </div>

      {/* ── Footer nav ──────────────────────────────────────────── */}
      <div className="border-t border-slate-800 pt-4 flex items-center justify-between">
        <Link href="/learnings"
          className="text-xs text-slate-400 hover:text-sky-300">
          ← Back to Learnings
        </Link>
        <Link href="/pricing"
          className="text-xs text-slate-400 hover:text-sky-300">
          Upgrade plan →
        </Link>
      </div>

    </div>
  );
}
