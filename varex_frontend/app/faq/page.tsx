"use client";
import { useEffect, useState } from "react";
import { listFAQs } from "@/lib/api";
import type { FAQ } from "@/lib/types";

const CATEGORIES = ["all","hiring","consulting","platform","sap","security","devops","general"];

export default function FAQPage() {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [active, setActive] = useState("all");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    listFAQs(active === "all" ? undefined : active).then(setFaqs);
  }, [active]);

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <header>
        <h1 className="text-2xl font-semibold mb-1">Frequently Asked Questions</h1>
        <p className="text-sm text-slate-300">Find answers about hiring, consulting, platform, SAP, and more.</p>
      </header>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <button key={c} onClick={() => setActive(c)}
            className={`rounded-full px-3 py-1 text-xs capitalize border ${
              active === c ? "bg-sky-500 border-sky-500 text-white" : "border-slate-700 text-slate-300 hover:border-sky-500"
            }`}>
            {c}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {faqs.map((f) => (
          <div key={f.id} className="rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden">
            <button onClick={() => setOpen(open === f.id ? null : f.id)}
              className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-100 hover:text-sky-300">
              {f.question}
              <span className="ml-2 text-slate-400">{open === f.id ? "−" : "+"}</span>
            </button>
            {open === f.id && (
              <div className="px-4 pb-3 text-xs text-slate-300 border-t border-slate-800 pt-2">{f.answer}</div>
            )}
          </div>
        ))}
        {faqs.length === 0 && <p className="text-xs text-slate-400">No FAQs found for this category yet.</p>}
      </div>
    </div>
  );
}
