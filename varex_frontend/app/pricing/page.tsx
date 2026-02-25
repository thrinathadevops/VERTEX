"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSubscription } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";

const PLANS = [
  {
    key: "free", label: "Free", price: "₹0", period: "forever",
    highlight: false,
    features: [
      "Homepage & public pages",
      "Limited blog articles",
      "Service overview",
      "Contact & consultation form",
    ],
    cta: "Get started free",
  },
  {
    key: "monthly", label: "Monthly", price: "₹1,499", period: "/month",
    highlight: false,
    features: [
      "Everything in Free",
      "Advanced DevSecOps courses",
      "Architecture deep dives",
      "Workshop recordings",
      "Case studies",
      "Downloadable templates",
    ],
    cta: "Subscribe monthly",
  },
  {
    key: "quarterly", label: "Quarterly", price: "₹3,999", period: "/quarter",
    highlight: true,  // most popular
    features: [
      "Everything in Monthly",
      "Interview prep content",
      "All blog archives",
      "Priority support",
      "Save ₹1,498 vs monthly",
    ],
    cta: "Best value",
  },
  {
    key: "enterprise", label: "Enterprise", price: "Custom", period: "",
    highlight: false,
    features: [
      "Private training content",
      "Custom dashboards",
      "Internal reports",
      "Dedicated workshop materials",
      "Dedicated account manager",
      "SLA-backed support",
    ],
    cta: "Contact sales",
  },
];

export default function PricingPage() {
  const router  = useRouter();
  const user    = getUserFromCookies();
  const [loading, setLoading] = useState<string | null>(null);
  const [error,   setError]   = useState<string | null>(null);

  const handleSubscribe = async (planKey: string) => {
    if (!user) { router.push("/register"); return; }
    if (planKey === "free") { router.push("/dashboard"); return; }
    if (planKey === "enterprise") { router.push("/contact?service=consulting"); return; }
    setLoading(planKey); setError(null);
    try {
      await createSubscription(planKey);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Something went wrong.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold mb-2">Simple, transparent pricing</h1>
        <p className="text-sm text-slate-300 max-w-md mx-auto">
          Choose the plan that fits your learning and hiring goals. Upgrade or cancel anytime.
        </p>
      </header>

      {error && (
        <div className="mx-auto max-w-md rounded-lg border border-red-700/50 bg-red-950/30 px-4 py-3 text-xs text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
        {PLANS.map((plan) => (
          <div key={plan.key}
            className={`relative rounded-2xl border p-5 flex flex-col ${
              plan.highlight
                ? "border-sky-500 bg-sky-950/40 shadow-lg shadow-sky-500/10"
                : "border-slate-800 bg-slate-900/70"
            }`}
          >
            {plan.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-sky-500 px-3 py-0.5 text-[10px] font-semibold text-white whitespace-nowrap">
                Most Popular
              </span>
            )}
            <div className="mb-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{plan.label}</p>
              <p className="text-3xl font-bold text-slate-50">
                {plan.price}
                <span className="text-sm font-normal text-slate-400">{plan.period}</span>
              </p>
            </div>
            <ul className="space-y-2 flex-1 mb-5">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-xs text-slate-300">
                  <span className="mt-0.5 text-emerald-400 flex-shrink-0">✓</span>{f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleSubscribe(plan.key)}
              disabled={loading === plan.key}
              className={`w-full rounded-lg px-3 py-2 text-xs font-semibold transition disabled:opacity-60 ${
                plan.highlight
                  ? "bg-sky-500 text-white hover:bg-sky-400"
                  : "border border-slate-600 text-slate-100 hover:border-sky-500 hover:text-sky-300"
              }`}
            >
              {loading === plan.key ? "Processing..." : plan.cta}
            </button>
          </div>
        ))}
      </div>

      {/* Access matrix */}
      <section className="max-w-3xl mx-auto rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="px-4 py-3 text-left text-slate-300 font-medium">Feature</th>
              {["Guest","Free","Premium","Enterprise"].map(h => (
                <th key={h} className="px-3 py-3 text-center text-slate-300 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {[
              ["Public pages & blog previews",  "✓","✓","✓","✓"],
              ["Full blog articles",            "−","✓","✓","✓"],
              ["DevSecOps courses",             "−","−","✓","✓"],
              ["Workshop recordings",           "−","−","✓","✓"],
              ["Architecture deep dives",       "−","−","✓","✓"],
              ["Downloadable templates",        "−","−","✓","✓"],
              ["Interview prep content",        "−","−","✓","✓"],
              ["Private training content",      "−","−","−","✓"],
              ["Custom dashboards",             "−","−","−","✓"],
              ["Internal reports",              "−","−","−","✓"],
              ["Dedicated account manager",     "−","−","−","✓"],
            ].map(([feature, ...checks]) => (
              <tr key={feature} className="hover:bg-slate-800/20">
                <td className="px-4 py-2.5 text-slate-200">{feature}</td>
                {checks.map((c, i) => (
                  <td key={i} className={`px-3 py-2.5 text-center font-medium ${c === "✓" ? "text-emerald-400" : "text-slate-600"}`}>{c}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
