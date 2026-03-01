// PATH: app/blog/sap/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listFreeContent, listPremiumContent } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";
import type { ContentItem } from "@/lib/types";
import { Boxes, Calendar, Clock3, Lock } from "lucide-react";

export default function SAPSDBlogPage() {
  const user      = getUserFromCookies();
  const isPremium = user && ["premium", "enterprise", "admin"].includes(user.role);
  const [items,   setItems]   = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [free, premium] = await Promise.all([
          listFreeContent(),
          isPremium ? listPremiumContent() : Promise.resolve([]),
        ]);
        const all = [...free, ...premium];
        setItems(all.filter((item) => item.category === "sap"));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const readingMins = (body: string) =>
    Math.max(1, Math.ceil((body?.split(" ").length ?? 0) / 200));

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/blog" className="hover:text-sky-300">Blog</Link>
        <span>/</span>
        <span className="text-slate-300">SAP SD</span>
      </nav>

      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <Boxes className="h-7 w-7 text-amber-300" />
          <h1 className="text-2xl font-bold">SAP SD</h1>
        </div>
        <p className="text-sm text-slate-300 max-w-lg">SAP SD configuration, integration, billing, and delivery management.</p>
      </header>

      <hr className="border-slate-800" />

      {loading ? (
        <div className="flex items-center justify-center min-h-[30vh]">
          <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <Boxes className="h-8 w-8 text-amber-300 mx-auto" />
          <p className="text-sm text-slate-400">No articles yet in this category.</p>
          <Link href="/blog" className="text-xs text-sky-400 hover:text-sky-300">← Back to all posts</Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((item) => {
            const blurred = item.access_level === "premium" && !isPremium;
            return (
              <Link key={item.id} href={`/blog/${item.slug ?? item.id}`}>
                <article className="group rounded-2xl border border-slate-800 bg-slate-900/70
                  p-4 hover:border-sky-600/70 transition cursor-pointer h-full flex flex-col">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h2 className="text-sm font-semibold text-slate-100 line-clamp-2
                      group-hover:text-sky-300 transition flex-1">{item.title}</h2>
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

      <div className="border-t border-slate-800 pt-4">
        <Link href="/blog" className="text-xs text-slate-400 hover:text-sky-300">← All categories</Link>
      </div>
    </div>
  );
}
