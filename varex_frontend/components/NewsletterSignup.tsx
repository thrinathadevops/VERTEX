"use client";

import { useState } from "react";
import { submitLead } from "@/lib/api";

export default function NewsletterSignup() {
  const [email,     setEmail]     = useState("");
  const [name,      setName]      = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [state,     setState]     = useState<"idle" | "success" | "error">("idle");
  const [errorMsg,  setErrorMsg]  = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    setState("idle");
    try {
      await submitLead({
        name:             name || email.split("@")[0],
        email,
        service_interest: "newsletter",
        message:          "Newsletter signup",
      });
      setState("success");
      setEmail("");
      setName("");
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail ?? "Something went wrong. Try again.");
      setState("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="rounded-2xl border border-sky-800/40 bg-sky-950/20 p-6 sm:p-8">
      <div className="max-w-xl mx-auto text-center space-y-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-sky-400">
          Stay Sharp
        </p>
        <h2 className="text-xl font-bold">
          Weekly DevSecOps & Architecture insights
        </h2>
        <p className="text-sm text-slate-300">
          One email per week. Real case studies, architecture breakdowns, and
          interview patterns — straight from our consulting work.
        </p>

        {state === "success" ? (
          <div className="rounded-xl border border-emerald-700/40 bg-emerald-950/30 px-6 py-5 space-y-1">
            <p className="text-2xl">🎉</p>
            <p className="text-sm font-semibold text-emerald-300">You are in!</p>
            <p className="text-xs text-slate-300">
              Check your inbox for a confirmation. First issue lands this week.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                placeholder="Your name (optional)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5
                  text-xs text-slate-100 placeholder:text-slate-500
                  focus:border-sky-500 focus:outline-none"
              />
              <input
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5
                  text-xs text-slate-100 placeholder:text-slate-500
                  focus:border-sky-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={submitting}
                className="flex-shrink-0 rounded-lg bg-sky-500 px-4 py-2.5 text-xs font-semibold
                  text-white hover:bg-sky-400 disabled:opacity-60 transition whitespace-nowrap"
              >
                {submitting ? "Subscribing..." : "Subscribe free →"}
              </button>
            </div>

            {state === "error" && (
              <p className="text-[11px] text-red-400">{errorMsg}</p>
            )}

            <p className="text-[11px] text-slate-500">
              No spam. Unsubscribe anytime. Read by 500+ engineers.
            </p>
          </form>
        )}

        {/* Trust badges */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          {[
            { icon: "🔒", label: "No spam ever"      },
            { icon: "📩", label: "1 email / week"    },
            { icon: "👥", label: "500+ subscribers"  },
          ].map((b) => (
            <div key={b.label} className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span>{b.icon}</span>
              <span>{b.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
