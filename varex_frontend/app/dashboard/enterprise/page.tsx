"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMe, getMySubscription } from "@/lib/api";
import type { User, Subscription } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function entFetch<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

interface Workshop { id: string; title: string; slug: string; status: string; scheduled_date?: string; seats_booked: number; max_seats: number; }
interface Lead     { id: string; name: string; service_interest: string; status: string; created_at: string; }

export default function EnterpriseDashboardPage() {
  const router = useRouter();
  const [user,         setUser]         = useState<User | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [workshops,    setWorkshops]    = useState<Workshop[]>([]);
  const [leads,        setLeads]        = useState<Lead[]>([]);
  const [loading,      setLoading]      = useState(true);

  useEffect(() => {
    const token = document.cookie.match(/access_token=([^;]+)/)?.[1] ?? "";
    Promise.all([getMe(), getMySubscription()])
      .then(([me, sub]) => {
        if (!["enterprise", "admin"].includes(me.role)) {
          router.replace("/dashboard");
          return;
        }
        setUser(me);
        setSubscription(sub);
        Promise.all([
          entFetch<Workshop[]>("/workshops", token),
          entFetch<Lead[]>("/leads",         token),
        ]).then(([ws, ls]) => {
          setWorkshops(ws);
          setLeads(ls.slice(0, 5));
        });
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="h-6 w-6 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
    </div>
  );
  if (!user) return null;

  const daysLeft = subscription?.expiry_date
    ? Math.max(0, Math.ceil((new Date(subscription.expiry_date).getTime() - Date.now()) / 86400000))
    : null;

  const upcomingWorkshops = workshops.filter((w) => ["upcoming","open"].includes(w.status));

  return (
    <div className="space-y-6 max-w-5xl mx-auto">

      {/* ── Header ──────────────────────────────────────────── */}
      <header className="rounded-2xl border border-amber-700/40 bg-amber-950/20 p-5
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🏢</span>
            <h1 className="text-xl font-bold">Enterprise Portal</h1>
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
              Enterprise
            </span>
          </div>
          <p className="text-xs text-slate-300">Welcome back, <strong>{user.name}</strong></p>
          {user.company && (
            <p className="text-xs text-slate-400 mt-0.5">🏢 {user.company}</p>
          )}
        </div>
        <div className="text-right">
          {daysLeft !== null ? (
            <>
              <p className="text-2xl font-bold text-amber-300">{daysLeft}</p>
              <p className="text-[11px] text-slate-400">days remaining</p>
            </>
          ) : (
            <p className="text-xs text-slate-400">Custom plan · No expiry</p>
          )}
        </div>
      </header>

      {/* ── Quick access cards ───────────────────────────────── */}
      <section>
        <h2 className="text-sm font-semibold mb-3">Quick Access</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/learnings",  icon: "📚", label: "Private Training",   desc: "Exclusive course library"      },
            { href: "/workshops",  icon: "🎓", label: "Dedicated Workshops", desc: "Your booked sessions"          },
            { href: "/portfolio",  icon: "🗂", label: "Case Studies",        desc: "Reference architecture"        },
            { href: "/contact",    icon: "📞", label: "Account Manager",     desc: "Get dedicated support"         },
          ].map((item) => (
            <Link key={item.label} href={item.href}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4
                hover:border-amber-600/60 transition space-y-1 cursor-pointer">
              <span className="text-2xl">{item.icon}</span>
              <p className="text-sm font-semibold text-slate-100">{item.label}</p>
              <p className="text-xs text-slate-400">{item.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Subscription details ─────────────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
        <h2 className="text-sm font-semibold">Subscription Details</h2>
        <div className="grid gap-3 sm:grid-cols-3 text-xs">
          <div>
            <p className="text-slate-400 mb-0.5">Plan</p>
            <p className="font-semibold capitalize text-amber-300">
              {subscription?.plan_type ?? "Enterprise"}
            </p>
          </div>
          <div>
            <p className="text-slate-400 mb-0.5">Status</p>
            <p className={`font-semibold capitalize ${
              subscription?.status === "active" ? "text-emerald-300" : "text-red-300"
            }`}>
              {subscription?.status ?? "Active"}
            </p>
          </div>
          <div>
            <p className="text-slate-400 mb-0.5">Valid Until</p>
            <p className="font-semibold text-slate-200">
              {subscription?.expiry_date
                ? new Date(subscription.expiry_date).toLocaleDateString("en-IN", {
                    day: "numeric", month: "long", year: "numeric"
                  })
                : "No expiry (custom contract)"}
            </p>
          </div>
        </div>
        <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
          <p className="text-[11px] text-slate-400">
            Need to renew or update your plan?
          </p>
          <Link href="/contact?service=consulting"
            className="text-[11px] text-amber-400 hover:text-amber-300">
            Contact your account manager →
          </Link>
        </div>
      </section>

      {/* ── Upcoming workshops ───────────────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Upcoming Workshops</h2>
          <Link href="/workshops" className="text-[11px] text-sky-400 hover:text-sky-300">
            View all →
          </Link>
        </div>
        {upcomingWorkshops.length === 0 ? (
          <p className="px-4 py-6 text-xs text-slate-400 text-center">No upcoming workshops scheduled.</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-left">
                {["Workshop","Date","Seats","Status"].map((h) => (
                  <th key={h} className="px-4 py-2 text-slate-400 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {upcomingWorkshops.map((w) => (
                <tr key={w.id} className="hover:bg-slate-800/20">
                  <td className="px-4 py-2.5">
                    <Link href={`/workshops/${w.slug}`} className="text-slate-200 hover:text-sky-300">
                      {w.title}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">
                    {w.scheduled_date
                      ? new Date(w.scheduled_date).toLocaleDateString("en-IN")
                      : "TBD"}
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">
                    {w.max_seats - w.seats_booked} left
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      w.status === "open"     ? "bg-emerald-500/20 text-emerald-300" :
                      w.status === "upcoming" ? "bg-sky-500/20 text-sky-300" :
                      "bg-slate-700 text-slate-300"
                    }`}>{w.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* ── Recent consultation activity ─────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800">
          <h2 className="text-sm font-semibold">Recent Consultation Activity</h2>
        </div>
        {leads.length === 0 ? (
          <p className="px-4 py-6 text-xs text-slate-400 text-center">No consultation history yet.</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-left">
                {["Contact","Service Requested","Status","Date"].map((h) => (
                  <th key={h} className="px-4 py-2 text-slate-400 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {leads.map((l) => (
                <tr key={l.id} className="hover:bg-slate-800/20">
                  <td className="px-4 py-2.5 text-slate-200">{l.name}</td>
                  <td className="px-4 py-2.5 text-slate-300">{l.service_interest}</td>
                  <td className="px-4 py-2.5">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      l.status === "converted" ? "bg-purple-500/20 text-purple-300" :
                      l.status === "new"       ? "bg-emerald-500/20 text-emerald-300" :
                      "bg-slate-700 text-slate-300"
                    }`}>{l.status}</span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">
                    {new Date(l.created_at).toLocaleDateString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* ── Support CTA ──────────────────────────────────────── */}
      <div className="rounded-2xl border border-amber-700/30 bg-amber-950/10 p-4
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-amber-100">Need dedicated support?</p>
          <p className="text-xs text-slate-400 mt-0.5">
            Your enterprise plan includes a dedicated account manager.
          </p>
        </div>
        <Link href="/contact?service=consulting"
          className="flex-shrink-0 rounded-md bg-amber-500 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-400">
          Contact account manager
        </Link>
      </div>

    </div>
  );
}
