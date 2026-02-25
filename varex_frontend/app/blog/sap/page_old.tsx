"use client";
import { useEffect, useState } from "react";
import { listFreeContent } from "@/lib/api";
import type { ContentItem } from "@/lib/types";
import ContentCard from "@/components/ContentCard";

export default function SapBlogPage() {
  const [items, setItems] = useState<ContentItem[]>([]);

  useEffect(() => {
    // Filter SAP content from free content list
    // In production, add ?category=sap query param to the backend
    listFreeContent().then(setItems);
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <span className="inline-block rounded-full bg-amber-500/20 px-2 py-0.5 text-[11px] text-amber-200 mb-2">SAP</span>
        <h1 className="text-2xl font-semibold mb-1">SAP SD Insights</h1>
        <p className="text-sm text-slate-300">
          Deep dives on SAP SD, S/4HANA, Order-to-Cash, pricing configuration, and integration patterns.
        </p>
      </header>

      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-xs text-slate-300 grid sm:grid-cols-3 gap-4">
        {["Order-to-Cash", "Pricing & Conditions", "S/4HANA Migration", "SD-MM Integration", "Billing Optimization", "SAP Support Packs"].map((topic) => (
          <div key={topic} className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 flex-shrink-0" />{topic}
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => <ContentCard key={item.id} item={item} />)}
        {items.length === 0 && <p className="text-xs text-slate-400">SAP SD articles coming soon. Subscribe to get notified.</p>}
      </div>
    </div>
  );
}
