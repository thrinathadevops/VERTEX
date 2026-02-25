"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import { getMe, createSubscription, listPremiumContent, listFreeContent } from "@/lib/api";
import type { User, ContentItem } from "@/lib/types";

// ── Inner component (runs inside ProtectedRoute) ──────────────────
function LearningsInner() {
  const [user,       setUser]       = useState<User | null>(null);
  const [items,      setItems]      = useState<ContentItem[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [billing,    setBilling]    = useState<"monthly" | "quarterly">("monthly");
  const [submitting, setSubmitting] = useState(false);
  const [message,    setMessage]    = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const me = await getMe();
        setUser(me);
        // load content based on role
        const isPremium = ["premium", "enterprise", "admin"].includes(me.role);
        const content   = isPremium
          ? await listPremiumContent()
          : await listFreeContent();
        setItems(content);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleUpgrade = async () => {
    setSubmitting(true);
    setMessage(null);
    try {
      await createSubscription(billing);
      setMessage({ type: "success", text: "✅ Subscription activated! Refreshing..." });
      setTimeout(() => window.location.reload(), 1500);
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err?.response?.data?.detail ?? "Unable to create subscription. Try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  const isPremium = user && ["premium", "enterprise", "admin"].includes(user.role);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">

      {/* ── Header ────────────────────────────────────────────── */}
      <header>
        <h1 className="text-2xl font-bold mb-1">
          {isPremium ? "Your Learning Library" : "Premium Learning Paths"}
        </h1>
        <p className="text-sm text-slate-300">
          {isPremium
            ? "Access all DevSecOps courses, architecture deep dives, and interview prep content."
            : "Upgrade to access guided architecture case studies, AI interview drills, and execution playbooks."}
        </p>
      </header>

      {/* ── Content grid (if premium) ─────────────────────────── */}
      {isPremium && items.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-200">
            All modules ({items.length})
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {items.map((item) => (
              <Link key={item.id} href={`/learnings/${item.slug ?? item.id}`}>
                <article className="group rounded-2xl border border-slate-800 bg-slate-900/70
                  p-4 hover:border-sky-600/70 cursor-pointer transition">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-sm font-semibold text-slate-100 line-clamp-2 group-hover:text-sky-300 transition">
                      {item.title}
                    </h3>
                    {item.access_level === "premium" && (
                      <span className="flex-shrink-0 rounded-full bg-amber-500/20 px-1.5 py-0.5 text-[9px] text-amber-300">
                        PRO
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {item.body?.replace(/<[^>]*>/g, "").slice(0, 120)}...
                  </p>
                  <p className="mt-3 text-[11px] text-sky-400 group-hover:text-sky-300">
                    Read module →
                  </p>
                </article>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── Pricing cards (if free user) ──────────────────────── */}
      {!isPremium && (
        <section className="grid gap-4 md:grid-cols-2">

          {/* Free card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-sm font-semibold mb-1">Free</h2>
            <p className="text-xs text-slate-400 mb-3">Great to explore the platform.</p>
            <ul className="mb-4 space-y-1.5 text-xs text-slate-300">
              {[
                "Access to public blog posts",
                "Limited system design notes",
                "Community updates",
                "Workshop listing",
              ].map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <span className="text-slate-500">•</span> {f}
                </li>
              ))}
            </ul>
            <button
              disabled
              className="w-full rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-400 cursor-not-allowed"
            >
              Current plan
            </button>
          </div>

          {/* Premium card */}
          <div className="rounded-2xl border border-sky-700/70 bg-sky-950/40 p-5">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-sm font-semibold">VAREX Premium</h2>
              <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-200">
                Recommended
              </span>
            </div>
            <p className="text-xs text-sky-100/80 mb-3">
              Weekly architecture drops, real interview transcripts, and execution drills.
            </p>

            {/* Billing toggle */}
            <div className="mb-4 flex gap-1.5 rounded-lg bg-slate-950/50 p-1 text-xs">
              <button
                onClick={() => setBilling("monthly")}
                className={`flex-1 rounded-md px-2 py-1.5 transition ${
                  billing === "monthly"
                    ? "bg-sky-500 text-white font-semibold"
                    : "text-slate-300 hover:text-slate-100"
                }`}
              >
                Monthly · ₹1,499
              </button>
              <button
                onClick={() => setBilling("quarterly")}
                className={`flex-1 rounded-md px-2 py-1.5 transition ${
                  billing === "quarterly"
                    ? "bg-sky-500 text-white font-semibold"
                    : "text-slate-300 hover:text-slate-100"
                }`}
              >
                Quarterly · ₹3,999
              </button>
            </div>

            <ul className="mb-4 space-y-1.5 text-xs text-sky-50">
              {[
                "Full access to all premium modules",
                "AI interview module",
                "Architecture review checklists",
                "Workshop recordings",
                "Downloadable templates",
              ].map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> {f}
                </li>
              ))}
            </ul>

            {message && (
              <p className={`mb-3 text-[11px] rounded-md px-3 py-2 ${
                message.type === "success"
                  ? "bg-emerald-950/50 text-emerald-300"
                  : "bg-red-950/50 text-red-300"
              }`}>
                {message.text}
              </p>
            )}

            <button
              onClick={handleUpgrade}
              disabled={submitting}
              className="w-full rounded-md bg-sky-500 px-3 py-2 text-xs font-semibold
                text-white hover:bg-sky-400 disabled:opacity-60 transition"
            >
              {submitting ? "Processing..." : `Upgrade · ${billing === "monthly" ? "₹1,499/mo" : "₹3,999/qtr"}`}
            </button>

            <p className="mt-2 text-center text-[10px] text-slate-400">
              Cancel anytime · Secure payment via Razorpay
            </p>
          </div>
        </section>
      )}

      {/* ── Free preview (always visible) ────────────────────── */}
      {!isPremium && items.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-200">Free previews</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {items.map((item) => (
              <Link key={item.id} href={`/learnings/${item.slug ?? item.id}`}>
                <article className="group rounded-2xl border border-slate-800 bg-slate-900/70
                  p-4 hover:border-sky-600/70 cursor-pointer transition">
                  <h3 className="text-sm font-semibold text-slate-100 line-clamp-2 mb-1
                    group-hover:text-sky-300 transition">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2 blur-[2px] group-hover:blur-none transition">
                    {item.body?.replace(/<[^>]*>/g, "").slice(0, 120)}...
                  </p>
                  <div className="mt-3 rounded-md border border-dashed border-sky-500/60
                    bg-sky-950/40 px-3 py-2 text-[11px] text-sky-100">
                    🔒 Premium insight — upgrade to read full module
                  </div>
                </article>
              </Link>
            ))}
          </div>
        </section>
      )}

    </div>
  );
}

// ── Page wrapper ──────────────────────────────────────────────────
export default function LearningsPage() {
  return (
    <ProtectedRoute>
      <LearningsInner />
    </ProtectedRoute>
  );
}