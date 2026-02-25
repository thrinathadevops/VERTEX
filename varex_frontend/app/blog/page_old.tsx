
"use client";

import { useEffect, useState } from "react";
import { listFreeContent, listPremiumContent } from "@/lib/api";
import type { ContentItem } from "@/lib/types";
import { getUserFromCookies } from "@/lib/auth";
import ContentCard from "@/components/ContentCard";

import { PAGE_META } from "@/lib/metadata";
export const metadata = PAGE_META.blog;


export default function BlogPage() {
  const [freeItems, setFreeItems] = useState<ContentItem[]>([]);
  const [premiumItems, setPremiumItems] = useState<ContentItem[]>([]);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    async function load() {
      const [freeData, premiumData] = await Promise.all([
        listFreeContent(),
        listPremiumContent().catch(() => []),
      ]);
      setFreeItems(freeData);
      setPremiumItems(premiumData);
      const user = getUserFromCookies();
      setIsPremium(user?.role === "premium_user" || user?.role === "admin");
    }
    load();
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold mb-2">Architecture blog</h1>
        <p className="text-sm text-slate-300">
          Curated notes on system design, resilience, and execution. Free posts first, then premium deep dives.
        </p>
      </header>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-slate-200">Free insights</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {freeItems.map((item) => (
            <ContentCard key={item.id} item={item} />
          ))}
          {freeItems.length === 0 && (
            <p className="text-xs text-slate-400">No free content yet. Check back soon.</p>
          )}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Premium deep dives</h2>
          {!isPremium && (
            <span className="text-[11px] text-slate-400">
              Sign in with a premium account to unlock full articles.
            </span>
          )}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {premiumItems.map((item) => (
            <ContentCard key={item.id} item={item} blurred={!isPremium} />
          ))}
          {premiumItems.length === 0 && (
            <p className="text-xs text-slate-400">Premium posts will appear here once published.</p>
          )}
        </div>
      </section>
    </div>
  );
}
