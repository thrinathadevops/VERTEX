// PATH: app/blog/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listFreeContent, listPremiumContent } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";
import type { ContentItem } from "@/lib/types";
import { Bot, Boxes, Calendar, Clock3, Cpu, Shield, Waypoints, Lock } from "lucide-react";

const CATEGORIES = [
  { slug: "devops",       label: "DevOps",        icon: Cpu,      color: "border-sky-700/50 text-sky-300" },
  { slug: "security",     label: "Cybersecurity", icon: Shield,   color: "border-red-700/50 text-red-300" },
  { slug: "sap",          label: "SAP SD",        icon: Boxes,    color: "border-amber-700/50 text-amber-300" },
  { slug: "architecture", label: "Architecture",  icon: Waypoints,color: "border-purple-700/50 text-purple-300" },
  { slug: "ai_hiring",    label: "AI Hiring",     icon: Bot,      color: "border-emerald-700/50 text-emerald-300" },
] as const;

type CategorySlug = typeof CATEGORIES[number]["slug"] | "all";

export default function BlogPage() {
  const user      = getUserFromCookies();
  const isPremium = user && ["premium", "enterprise", "admin"].includes(user.role);

  const [items,   setItems]   = useState<ContentItem[]>([]);
  const [filter,  setFilter]  = useState<CategorySlug>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [free, premium] = await Promise.all([
          listFreeContent(),
          isPremium ? listPremiumContent() : Promise.resolve([]),
        ]);
        setItems([...free, ...premium]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const readingMins = (body: string) =>
    Math.max(1, Math.ceil((body?.split(" ").length ?? 0) / 200));

  const shown = filter === "all"
    ? items
    : items.filter((i) => i.category === filter);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">

      {/* Header */}
      <header>
        <h1 className="text-2xl font-bold mb-1">Blog</h1>
        <p className="text-sm text-slate-300">
          Expert articles on DevSecOps, Cybersecurity, SAP SD, Architecture, and AI Hiring.
        </p>
      </header>

      {/* Category cards — click goes to dedicated category page */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {CATEGORIES.map((cat) => {
          const count = items.filter((i) => i.category === cat.slug).length;
          const Icon = cat.icon;
          return (
            <Link key={cat.slug} href={`/blog/${cat.slug}`}
              className={`rounded-2xl border bg-slate-900/70 p-3 hover:bg-slate-800/70
                transition cursor-pointer space-y-1 ${cat.color.split(" ")[0]}`}>
              <Icon className="h-5 w-5" />
              <p className={`text-xs font-semibold ${cat.color.split(" ")[1]}`}>{cat.label}</p>
              <p className="text-[11px] text-slate-500">{count} article{count !== 1 ? "s" : ""}</p>
            </Link>
          );
        })}
      </section>

      {/* Filter pills — for inline filtering without navigating */}
      <div className="flex flex-wrap gap-2">
        <button onClick={() => setFilter("all")}
          className={`rounded-full px-3 py-1 text-xs font-medium transition ${
            filter === "all" ? "bg-sky-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}>
          All posts {items.length > 0 && `(${items.length})`}
        </button>
        {CATEGORIES.map((cat) => (
          <button key={cat.slug} onClick={() => setFilter(cat.slug)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              filter === cat.slug ? "bg-sky-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Article grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[30vh]">
          <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
        </div>
      ) : shown.length === 0 ? (
        <div className="text-center py-12 space-y-2">
          <p className="text-sm text-slate-400">No articles in this category yet.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map((item) => {
            const blurred = item.access_level === "premium" && !isPremium;
            const cat = CATEGORIES.find((c) => c.slug === item.category);
            return (
              <Link key={item.id} href={`/blog/${item.slug ?? item.id}`}>
                <article className="group rounded-2xl border border-slate-800
                  bg-slate-900/70 p-4 hover:border-sky-600/70 transition cursor-pointer h-full flex flex-col">

                  {/* Category badge */}
                  {cat && (
                    <span className={`inline-flex items-center gap-1 self-start rounded-full
                      px-2 py-0.5 text-[10px] font-medium mb-2
                      ${cat.color.split(" ")[0].replace("border-", "bg-").replace("/50", "/20")}
                      ${cat.color.split(" ")[1]}`}>
                      <cat.icon className="h-3 w-3" /> {cat.label}
                    </span>
                  )}

                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h2 className="text-sm font-semibold text-slate-100 line-clamp-2
                      group-hover:text-sky-300 transition flex-1">
                      {item.title}
                    </h2>
                    {item.access_level === "premium" && (
                      <span className="flex-shrink-0 rounded-full bg-amber-500/20
                        px-1.5 py-0.5 text-[9px] text-amber-300">PRO</span>
                    )}
                  </div>

                  <p className={`text-xs text-slate-400 leading-relaxed line-clamp-3 flex-1 mb-3 ${
                    blurred ? "blur-[2px] group-hover:blur-none transition" : ""
                  }`}>
                    {item.body?.replace(/<[^>]*>/g, "").slice(0, 150)}...
                  </p>

                  {blurred && (
                    <div className="rounded-md border border-dashed border-sky-500/60
                      bg-sky-950/40 px-3 py-2 text-[11px] text-sky-100 mb-2">
                      <span className="inline-flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        Premium only - <Link href="/pricing" className="underline">upgrade to read</Link>
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-auto">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> {new Date(item.created_at).toLocaleDateString("en-IN")}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Clock3 className="h-3 w-3" /> {readingMins(item.body)} min read
                    </span>
                  </div>
                </article>
              </Link>
            );
          })}
        </div>
      )}

    </div>
  );
}
