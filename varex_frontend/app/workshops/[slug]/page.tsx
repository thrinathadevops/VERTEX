"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getWorkshop, registerWorkshop } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";
import type { Workshop } from "@/lib/types";

export default function WorkshopDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const user = getUserFromCookies();

  const [workshop, setWorkshop] = useState<Workshop | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [registering, setRegistering] = useState(false);
  const [regMessage, setRegMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!slug) return;
    getWorkshop(slug)
      .then(setWorkshop)
      .catch((err) => {
        setError(err?.response?.status === 404 ? "notfound" : "unknown");
      })
      .finally(() => setLoading(false));
  }, [slug]);

  const handleRegister = async () => {
    if (!user) { setRegMessage({ type: "error", text: "Please sign in to register." }); return; }
    if (!workshop) return;
    setRegistering(true);
    setRegMessage(null);
    try {
      await registerWorkshop(workshop.id);
      setRegMessage({ type: "success", text: "🎉 You are registered! Check your email for confirmation." });
      setWorkshop((w) => w ? { ...w, seats_booked: w.seats_booked + 1 } : w);
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? "Registration failed. Try again.";
      setRegMessage({ type: "error", text: detail });
    } finally {
      setRegistering(false);
    }
  };

  // ── Loading ───────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  // ── 404 ──────────────────────────────────────────────────────
  if (error === "notfound") return (
    <div className="max-w-xl mx-auto text-center py-20 space-y-3">
      <p className="text-4xl">🗓</p>
      <h1 className="text-xl font-semibold">Workshop not found</h1>
      <p className="text-sm text-slate-400">This workshop may have ended or been removed.</p>
      <Link href="/workshops" className="inline-block text-xs text-sky-400 hover:text-sky-300 mt-2">
        ← Back to Workshops
      </Link>
    </div>
  );

  if (!workshop) return null;

  const seatsLeft = workshop.max_seats - workshop.seats_booked;
  const seatsRatio = workshop.seats_booked / workshop.max_seats;
  const isFull = workshop.status === "full" || seatsLeft <= 0;
  const isCompleted = workshop.status === "completed";

  const STATUS_STYLES: Record<string, string> = {
    open: "bg-emerald-500/20 text-emerald-300",
    upcoming: "bg-sky-500/20 text-sky-300",
    full: "bg-red-500/20 text-red-300",
    completed: "bg-slate-700 text-slate-400",
  };

  const MODE_ICONS: Record<string, string> = {
    online: "💻 Online",
    offline: "📍 In-person",
    hybrid: "🔀 Hybrid",
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">

      {/* ── Breadcrumb ────────────────────────────────────────── */}
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/workshops" className="hover:text-sky-300">Workshops</Link>
        <span>/</span>
        <span className="text-slate-300 truncate max-w-[200px]">{workshop.title}</span>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────── */}
      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide
            ${STATUS_STYLES[workshop.status] ?? "bg-slate-700 text-slate-300"}`}>
            {workshop.status}
          </span>
          <span className="text-[11px] text-slate-400">{MODE_ICONS[workshop.mode]}</span>
        </div>
        <h1 className="text-3xl font-bold leading-snug">{workshop.title}</h1>
        <p className="text-sm text-slate-300">{workshop.description}</p>

        {/* ── Key details row ───────────────────────────────── */}
        <div className="flex flex-wrap gap-4 text-[11px] text-slate-400 pt-1">
          {workshop.scheduled_date && (
            <span>📅 {new Date(workshop.scheduled_date).toLocaleDateString("en-IN", {
              weekday: "short", day: "numeric", month: "long", year: "numeric"
            })}</span>
          )}
          <span>⏱ {workshop.duration_hours} hour{(workshop.duration_hours ?? 0) > 1 ? "s" : ""}</span>
          <span>💺 {seatsLeft > 0 ? `${seatsLeft} seats left` : "Fully booked"}</span>
          {workshop.price_inr !== undefined && (
            <span>💰 {workshop.price_inr === 0 ? "Free" : `₹${workshop.price_inr.toLocaleString("en-IN")}`}</span>
          )}
        </div>

        {/* ── Seat progress bar ─────────────────────────────── */}
        <div className="space-y-1">
          <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${seatsRatio >= 0.9 ? "bg-red-500" :
                  seatsRatio >= 0.6 ? "bg-amber-500" : "bg-emerald-500"
                }`}
              style={{ width: `${Math.min(seatsRatio * 100, 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500">
            {workshop.seats_booked} / {workshop.max_seats} seats filled
          </p>
        </div>
      </header>

      <hr className="border-slate-800" />

      {/* ── Curriculum ────────────────────────────────────────── */}
      {workshop.curriculum && (
        <section className="space-y-2">
          <h2 className="text-base font-semibold">📋 Curriculum</h2>
          <div
            className="prose prose-invert prose-sm max-w-none
              prose-headings:text-slate-100 prose-p:text-slate-300
              prose-li:text-slate-300 prose-li:marker:text-sky-400
              prose-strong:text-slate-100 prose-code:bg-slate-800
              prose-code:px-1 prose-code:rounded"
            dangerouslySetInnerHTML={{ __html: workshop.curriculum }}
          />
        </section>
      )}

      {/* ── Registration card ─────────────────────────────────── */}
      <section className={`rounded-2xl border p-5 space-y-4 ${isFull || isCompleted
          ? "border-slate-700 bg-slate-900/50"
          : "border-sky-700/50 bg-sky-950/30"
        }`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">
              {isCompleted ? "Workshop ended" : isFull ? "Fully booked" : "Reserve your seat"}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {isCompleted
                ? "This workshop has concluded. Check upcoming sessions."
                : isFull
                  ? "All seats are taken. Join the waitlist or check next batch."
                  : `Only ${seatsLeft} seat${seatsLeft > 1 ? "s" : ""} remaining.`}
            </p>
          </div>
          {workshop.price_inr !== undefined && !isCompleted && (
            <div className="text-right flex-shrink-0">
              <p className="text-xl font-bold text-sky-300">
                {workshop.price_inr === 0 ? "Free" : `₹${workshop.price_inr.toLocaleString("en-IN")}`}
              </p>
              <p className="text-[10px] text-slate-500">per seat</p>
            </div>
          )}
        </div>

        {regMessage && (
          <p className={`rounded-md px-3 py-2 text-xs ${regMessage.type === "success"
              ? "bg-emerald-950/50 text-emerald-300"
              : "bg-red-950/50 text-red-300"
            }`}>
            {regMessage.text}
          </p>
        )}

        {!isCompleted && (
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={handleRegister}
              disabled={isFull || registering}
              className={`flex-1 rounded-md px-4 py-2.5 text-xs font-semibold transition
                ${isFull
                  ? "border border-slate-600 text-slate-400 cursor-not-allowed"
                  : "bg-sky-500 text-white hover:bg-sky-400 disabled:opacity-60"
                }`}
            >
              {registering ? "Registering..." : isFull ? "Join Waitlist" : "Register Now"}
            </button>
            <Link href="/contact"
              className="flex-1 text-center rounded-md border border-slate-600 px-4 py-2.5
                text-xs text-slate-200 hover:border-sky-500 hover:text-sky-300">
              Ask a question
            </Link>
          </div>
        )}

        {isCompleted && (
          <Link href="/workshops"
            className="inline-block rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
            View upcoming workshops →
          </Link>
        )}

        {!user && !isCompleted && (
          <p className="text-[11px] text-slate-400 text-center">
            <Link href="/login" className="text-sky-400 hover:text-sky-300">Sign in</Link>
            {" "}or{" "}
            <Link href="/register" className="text-sky-400 hover:text-sky-300">create a free account</Link>
            {" "}to register
          </p>
        )}
      </section>

      {/* ── Footer nav ────────────────────────────────────────── */}
      <div className="border-t border-slate-800 pt-4">
        <Link href="/workshops" className="text-xs text-slate-400 hover:text-sky-300">
          ← Back to Workshops
        </Link>
      </div>

    </div>
  );
}