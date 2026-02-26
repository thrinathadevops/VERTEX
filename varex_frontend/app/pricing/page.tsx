// PATH: varex_frontend/app/pricing/page.tsx
// FIX 2.5: handleSubscribe now opens Razorpay modal first, only activates after payment
// FIX 2.6: role === "premium" (not "premium_user")

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/lib/api";
import { initiatePayment } from "@/lib/razorpay";
import type { User } from "@/lib/types";

const PLANS = [
  {
    key:      "monthly" as const,
    label:    "Monthly",
    price:    "₹1,499",
    paise:    149900,
    features: ["All premium modules", "Workshop recordings", "Priority support"],
  },
  {
    key:      "quarterly" as const,
    label:    "Quarterly",
    price:    "₹3,999",
    paise:    399900,
    badge:    "Best Value",
    features: ["Everything in Monthly", "3-month access", "Save ₹498"],
  },
];

export default function PricingPage() {
  const router  = useRouter();
  const [user,    setUser]    = useState<User | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    getMe().then(setUser).catch(() => {});
  }, []);

  async function handleSubscribe(planKey: "monthly" | "quarterly") {
    if (!user) { router.push("/login"); return; }
    setLoading(planKey);
    setError(null);

    try {
      // Step 1 — Create Razorpay order via Next.js API route
      const orderRes = await fetch("/api/razorpay/create-order", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ plan_type: planKey }),
      });
      if (!orderRes.ok) throw new Error("Could not create payment order");
      const { razorpay_order_id, id: subscription_id } = await orderRes.json();

      // Step 2 — Open Razorpay modal; payment collected here
      await initiatePayment({
        order_id:       razorpay_order_id,
        subscription_id,
        amount:         PLANS.find((p) => p.key === planKey)!.paise,
        user_name:      user.name,
        user_email:     user.email,
        // onSuccess: verify + activate is handled inside initiatePayment
      });

      // Step 3 — Redirect to dashboard on success
      router.push("/dashboard/premium");
    } catch (err: any) {
      setError(err?.message ?? "Payment failed. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen py-20 px-4">
      <div className="max-w-4xl mx-auto text-center mb-14">
        <h1 className="text-3xl font-bold mb-3">Choose Your Plan</h1>
        <p className="text-slate-400">
          Unlock premium modules, workshop recordings, and expert support.
        </p>
      </div>

      {error && (
        <p className="text-center text-red-400 mb-6">{error}</p>
      )}

      <div className="grid gap-6 sm:grid-cols-3 max-w-4xl mx-auto">
        {/* Free */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-lg font-bold mb-1">Free</p>
          <p className="text-3xl font-extrabold mb-4">₹0</p>
          <ul className="text-sm text-slate-400 space-y-2 mb-6">
            <li>✓ Free articles</li>
            <li>✓ Workshop listings</li>
            <li>✓ Community access</li>
          </ul>
          <button
            disabled
            className="w-full rounded-xl py-2 text-sm bg-slate-800 text-slate-500 cursor-not-allowed"
          >
            {user ? "Current Plan" : "Get Started Free"}
          </button>
        </div>

        {/* Monthly & Quarterly */}
        {PLANS.map((plan) => (
          <div
            key={plan.key}
            className="relative rounded-2xl border border-sky-600/50 bg-slate-900/80 p-6"
          >
            {plan.badge && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-sky-600 px-3 py-0.5 text-xs font-semibold">
                {plan.badge}
              </span>
            )}
            <p className="text-lg font-bold mb-1">{plan.label}</p>
            <p className="text-3xl font-extrabold mb-1">{plan.price}</p>
            <p className="text-xs text-slate-500 mb-4">
              {plan.key === "monthly" ? "per month" : "per quarter"}
            </p>
            <ul className="text-sm text-slate-400 space-y-2 mb-6">
              {plan.features.map((f) => <li key={f}>✓ {f}</li>)}
            </ul>
            <button
              onClick={() => handleSubscribe(plan.key)}
              disabled={!!loading || user?.role === "premium" || user?.role === "enterprise"}
              className="w-full rounded-xl py-2 text-sm font-semibold bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading === plan.key
                ? "Processing…"
                : user?.role === "premium" || user?.role === "enterprise"
                ? "Current Plan"
                : "Subscribe"}
            </button>
          </div>
        ))}
      </div>

      {/* Enterprise */}
      <div className="max-w-4xl mx-auto mt-6 rounded-2xl border border-amber-700/40 bg-amber-950/10 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-bold text-lg">Enterprise</p>
          <p className="text-sm text-slate-400">Custom pricing · Dedicated support · Team onboarding</p>
        </div>
        <a
          href="/contact"
          className="rounded-xl px-6 py-2 bg-amber-600 hover:bg-amber-500 text-sm font-semibold transition"
        >
          Contact Sales
        </a>
      </div>
    </div>
  );
}
