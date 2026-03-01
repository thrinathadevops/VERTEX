"use client";

import { useState } from "react";
import { submitLead } from "@/lib/api";
import AnimateIn from "@/components/AnimateIn";
import { Mail, Lock, Users, Send, CheckCircle2 } from "lucide-react";

export default function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [state, setState] = useState<"idle" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    setState("idle");
    try {
      await submitLead({
        name: name || email.split("@")[0],
        email,
        service_interest: "newsletter",
        message: "Newsletter signup",
      });
      await fetch("/api/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: email,
          name: name || email.split("@")[0],
          template: "welcome",
        })
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
    <AnimateIn>
      <section className="relative rounded-3xl border border-sky-800/30 bg-gradient-to-br from-sky-950/40 via-slate-900/60 to-indigo-950/40 p-8 sm:p-12 overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute top-0 left-1/4 w-64 h-64 bg-sky-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-1/4 w-48 h-48 bg-indigo-500/10 rounded-full blur-[80px]" />

        <div className="relative z-10 max-w-xl mx-auto text-center space-y-5">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-sky-500/10 text-sky-400 border border-sky-500/20 mx-auto">
            <Mail className="w-7 h-7" />
          </div>

          <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase">
            Stay Sharp
          </h2>
          <h3 className="text-2xl md:text-3xl font-extrabold text-white">
            Weekly DevSecOps & Architecture Insights
          </h3>
          <p className="text-base text-slate-300 leading-relaxed">
            One email per week. Real case studies, architecture breakdowns, and
            interview patterns — straight from our consulting work.
          </p>

          {state === "success" ? (
            <div className="rounded-xl border border-emerald-700/40 bg-emerald-950/30 px-6 py-6 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-300 mx-auto" />
              <p className="text-base font-bold text-emerald-300">You&apos;re in!</p>
              <p className="text-sm text-slate-300">
                Check your inbox for a confirmation. First issue lands this week.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4 pt-2">
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Your name (optional)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3
                    text-sm text-slate-100 placeholder:text-slate-500
                    focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50 transition-all"
                />
                <input
                  type="email"
                  required
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3
                    text-sm text-slate-100 placeholder:text-slate-500
                    focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50 transition-all"
                />
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 hover:bg-sky-400 px-6 py-3 text-sm font-bold
                    text-white disabled:opacity-60 transition-all shadow-lg shadow-sky-500/20 hover:shadow-sky-500/30 whitespace-nowrap"
                >
                  <Send className="w-4 h-4" />
                  {submitting ? "Subscribing..." : "Subscribe free"}
                </button>
              </div>

              {state === "error" && (
                <p className="text-sm text-red-400">{errorMsg}</p>
              )}

              <div className="flex flex-wrap items-center justify-center gap-6 pt-1 text-sm text-slate-500">
                <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5" /> No spam ever</span>
                <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5" /> 1 email / week</span>
                <span className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> 500+ subscribers</span>
              </div>
            </form>
          )}
        </div>
      </section>
    </AnimateIn>
  );
}
