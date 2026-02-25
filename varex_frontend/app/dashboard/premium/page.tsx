// PATH: app/dashboard/premium/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getMe, getMySubscription, listPremiumContent } from "@/lib/api";
import type { User, Subscription, ContentItem } from "@/lib/types";

export default function PremiumDashboardPage() {
  const router = useRouter();
  const [user,         setUser]         = useState<User | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [items,        setItems]        = useState<ContentItem[]>([]);
  const [loading,      setLoading]      = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [me, sub] = await Promise.all([getMe(), getMySubscription()]);
        if (!["premium", "admin"].includes(me.role)) {
          router.replace("/dashboard");
          return;
        }
        setUser(me);
        setSubscription(sub);
        const content = await listPremiumContent();
        setItems(content.slice(0, 6));
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
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

  const expiryWarning = daysLeft !== null && daysLeft <= 7;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* Header */}
      <header className="rounded-2xl border border-amber-700/30 bg-amber-950/20 p-5
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⭐</span>
            <h1 className="text-xl font-bold">Premium Dashboard</h1>
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
              Premium
            </span>
          </div>
          <p className="text-xs text-slate-300">Welcome back, <strong>{user.name}</strong></p>
        </div>
        <div className="text-right">
          {daysLeft !== null ? (
            <>
              <p className={`text-2xl font-bold ${expiryWarning ? "text-red-400" : "text-amber-300"}`}>
                {daysLeft}
              </p>
              <p className="text-[11px] text-slate-400">days remaining</p>
              {expiryWarning && (
                <Link href="/pricing"
                  className="mt-1 inline-block rounded-md bg-red-500/20 px-2 py-0.5
                    text-[10px] text-red-300 hover:bg-red-500/30">
                  Renew now →
                </Link>
              )}
            </>
          ) : (
            <p className="text-xs text-slate-400">Active subscription</p>
          )}
        </div>
      </header>

      {/* Quick stats */}
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { label: "Plan",       value: subscription?.plan_type?.replace("_", " ") ?? "Premium", icon: "📋" },
          { label: "Status",     value: subscription?.status ?? "Active",                         icon: "✅" },
          { label: "Valid Until",
            value: subscription?.expiry_date
              ? new Date(subscription.expiry_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })
              : "—",
            icon: "📅"
          },
        ].map((s) => (
          <div key={s.label}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-400">{s.label}</p>
              <span>{s.icon}</span>
            </div>
            <p className="text-sm font-semibold capitalize text-slate-100">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Quick access */}
      <section>
        <h2 className="text-sm font-semibold mb-3">Your Premium Access</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/learnings",   icon: "📚", label: "All Modules",        desc: "Full content library"       },
            { href: "/workshops",   icon: "🎓", label: "Workshops",          desc: "Recordings + upcoming"      },
            { href: "/blog",        icon: "📝", label: "Premium Articles",   desc: "PRO-tagged deep dives"      },
            { href: "/contact",     icon: "📞", label: "Priority Support",   desc: "Faster response SLA"        },
          ].map((item) => (
            <Link key={item.label} href={item.href}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4
                hover:border-amber-600/60 transition space-y-1">
              <span className="text-2xl">{item.icon}</span>
              <p className="text-xs font-semibold text-slate-100">{item.label}</p>
              <p className="text-[11px] text-slate-400">{item.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Recent premium content */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Latest Premium Modules</h2>
          <Link href="/learnings" className="text-[11px] text-sky-400 hover:text-sky-300">
            View all →
          </Link>
        </div>
        {items.length === 0 ? (
          <p className="px-4 py-6 text-xs text-slate-400 text-center">No content yet.</p>
        ) : (
          <div className="divide-y divide-slate-800/50">
            {items.map((item) => (
              <Link key={item.id} href={`/learnings/${item.slug ?? item.id}`}
                className="flex items-center justify-between px-4 py-3
                  hover:bg-slate-800/30 transition group">
                <div>
                  <p className="text-xs font-medium text-slate-200 group-hover:text-sky-300 transition">
                    {item.title}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    {new Date(item.created_at).toLocaleDateString("en-IN")}
                  </p>
                </div>
                <span className="text-[11px] text-sky-400 group-hover:text-sky-300">Read →</span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Upgrade CTA if expiry soon */}
      {expiryWarning && (
        <div className="rounded-2xl border border-red-700/30 bg-red-950/10 p-4
          flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-red-200">⏰ Your plan expires in {daysLeft} days</p>
            <p className="text-xs text-slate-400 mt-0.5">Renew now to keep uninterrupted access.</p>
          </div>
          <Link href="/pricing"
            className="flex-shrink-0 rounded-md bg-red-500 px-4 py-2 text-xs font-semibold
              text-white hover:bg-red-400 transition">
            Renew subscription
          </Link>
        </div>
      )}

    </div>
  );
}
