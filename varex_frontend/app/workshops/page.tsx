"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listWorkshops, registerWorkshop } from "@/lib/api";
import { getUserFromCookies } from "@/lib/auth";
import type { Workshop } from "@/lib/types";

export default function WorkshopsPage() {
  const [workshops,   setWorkshops]   = useState<Workshop[]>([]);
  const [registering, setRegistering] = useState<string | null>(null);
  const [messages,    setMessages]    = useState<Record<string, { type: "success" | "error"; text: string }>>({});
  const isLoggedIn = !!getUserFromCookies();

  useEffect(() => {
    listWorkshops().then(setWorkshops).catch(console.error);
  }, []);

  const handleRegister = async (id: string) => {
    setRegistering(id);
    try {
      await registerWorkshop(id);
      setMessages((m) => ({ ...m, [id]: { type: "success", text: "✅ Registered successfully!" } }));
      // update seat count locally
      setWorkshops((ws) =>
        ws.map((w) => w.id === id ? { ...w, seats_booked: w.seats_booked + 1 } : w)
      );
    } catch (err: any) {
      setMessages((m) => ({
        ...m,
        [id]: { type: "error", text: err?.response?.data?.detail ?? "Registration failed. Try again." },
      }));
    } finally {
      setRegistering(null);
    }
  };

  const STATUS_STYLES: Record<string, string> = {
    open:      "bg-emerald-500/20 text-emerald-300",
    upcoming:  "bg-sky-500/20 text-sky-300",
    full:      "bg-red-500/20 text-red-300",
    completed: "bg-slate-700 text-slate-400",
  };

  const MODE_ICONS: Record<string, string> = {
    online:  "💻 Online",
    offline: "📍 In-person",
    hybrid:  "🔀 Hybrid",
  };

  return (
    <div className="space-y-8">

      {/* ── Header ────────────────────────────────────────────── */}
      <header>
        <h1 className="text-2xl font-bold mb-1">Workshops & Training</h1>
        <p className="text-sm text-slate-300">
          Hands-on workshops on DevSecOps, Kubernetes, Cloud Architecture, and SAP SD.
        </p>
      </header>

      {/* ── Grid ──────────────────────────────────────────────── */}
      <div className="grid gap-5 md:grid-cols-2">
        {workshops.map((w) => {
          const seatsLeft  = w.max_seats - w.seats_booked;
          const seatsRatio = w.seats_booked / w.max_seats;
          const isFull     = w.status === "full" || seatsLeft <= 0;
          const isCompleted = w.status === "completed";
          const msg        = messages[w.id];

          return (
            <div key={w.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 flex flex-col gap-3">

              {/* Title + status */}
              <div className="flex items-start justify-between gap-2">
                <Link href={`/workshops/${w.slug}`}
                  className="text-sm font-semibold text-slate-100 hover:text-sky-300 transition line-clamp-2">
                  {w.title}
                </Link>
                <span className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium
                  ${STATUS_STYLES[w.status] ?? "bg-slate-700 text-slate-300"}`}>
                  {w.status}
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-slate-300 line-clamp-2">{w.description}</p>

              {/* Meta row */}
              <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                <span>⏱ {w.duration_hours}h</span>
                <span>{MODE_ICONS[w.mode] ?? w.mode}</span>
                <span>💺 {seatsLeft > 0 ? `${seatsLeft} seats left` : "Fully booked"}</span>
                {w.scheduled_date && (
                  <span>📅 {new Date(w.scheduled_date).toLocaleDateString("en-IN")}</span>
                )}
              </div>

              {/* Seat progress bar */}
              <div className="space-y-1">
                <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      seatsRatio >= 0.9 ? "bg-red-500" :
                      seatsRatio >= 0.6 ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(seatsRatio * 100, 100)}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-500">
                  {w.seats_booked} / {w.max_seats} seats filled
                </p>
              </div>

              {/* Price */}
              {w.price_inr !== undefined && (
                <p className="text-base font-bold text-sky-400">
                  {w.price_inr === 0 ? "Free" : `₹${w.price_inr.toLocaleString("en-IN")}`}
                  <span className="text-xs font-normal text-slate-400"> / seat</span>
                </p>
              )}

              {/* Message */}
              {msg && (
                <p className={`rounded-md px-3 py-2 text-xs ${
                  msg.type === "success"
                    ? "bg-emerald-950/50 text-emerald-300"
                    : "bg-red-950/50 text-red-300"
                }`}>
                  {msg.text}
                </p>
              )}

              {/* Actions */}
              <div className="flex gap-2 mt-auto">
                <Link href={`/workshops/${w.slug}`}
                  className="flex-1 text-center rounded-md border border-slate-700
                    px-3 py-2 text-xs text-slate-200 hover:border-sky-500 hover:text-sky-300 transition">
                  View details
                </Link>

                {!isCompleted && (
                  isLoggedIn ? (
                    <button
                      onClick={() => handleRegister(w.id)}
                      disabled={registering === w.id || isFull}
                      className={`flex-1 rounded-md px-3 py-2 text-xs font-semibold transition
                        disabled:opacity-50 ${
                          isFull
                            ? "border border-slate-600 text-slate-400 cursor-not-allowed"
                            : "bg-sky-500 text-white hover:bg-sky-400"
                        }`}
                    >
                      {registering === w.id ? "Registering..." : isFull ? "Fully booked" : "Register now"}
                    </button>
                  ) : (
                    <Link href="/login"
                      className="flex-1 text-center rounded-md border border-sky-500
                        px-3 py-2 text-xs text-sky-300 hover:bg-sky-500/10 transition">
                      Sign in to register
                    </Link>
                  )
                )}
              </div>

            </div>
          );
        })}

        {workshops.length === 0 && (
          <div className="col-span-full text-center py-12 space-y-2">
            <p className="text-2xl">🗓</p>
            <p className="text-sm text-slate-400">No upcoming workshops. Check back soon.</p>
            <Link href="/contact" className="text-xs text-sky-400 hover:text-sky-300">
              Request a custom workshop →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}