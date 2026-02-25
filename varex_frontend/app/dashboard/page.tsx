// PATH: varex_frontend/app/dashboard/page.tsx
// FIX: role === "premium_user" -> role === "premium" (Bug 2.6)
// FIX: role === "enterprise" added
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMe } from "@/lib/api";
import type { User } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((me) => {
        setUser(me);
        // Redirect to role-specific dashboard
        if (me.role === "admin")      { router.replace("/dashboard/admin");      return; }
        if (me.role === "enterprise") { router.replace("/dashboard/enterprise"); return; }
        if (me.role === "premium")    { router.replace("/dashboard/premium");    return; }
        // free_user stays on this base dashboard
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  if (!user) return null;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <header>
        <h1 className="text-xl font-bold">Welcome, {user.name}</h1>
        <p className="text-xs text-slate-400 mt-0.5 capitalize">
          Plan: <span className="text-sky-300">{user.role.replace("_", " ")}</span>
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link href="/learnings"
          className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-600/60 transition">
          <p className="text-lg mb-1">📚</p>
          <p className="text-sm font-semibold">Free Content</p>
          <p className="text-xs text-slate-400 mt-0.5">Access free articles and resources</p>
        </Link>
        <Link href="/workshops"
          className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-600/60 transition">
          <p className="text-lg mb-1">🎓</p>
          <p className="text-sm font-semibold">Workshops</p>
          <p className="text-xs text-slate-400 mt-0.5">Browse and register for workshops</p>
        </Link>
        <Link href="/pricing"
          className="rounded-2xl border border-amber-800/40 bg-amber-950/10 p-4 hover:border-amber-600/60 transition">
          <p className="text-lg mb-1">⭐</p>
          <p className="text-sm font-semibold text-amber-300">Upgrade to Premium</p>
          <p className="text-xs text-slate-400 mt-0.5">Unlock all modules and recordings</p>
        </Link>
        <Link href="/dashboard/settings"
          className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-600/60 transition">
          <p className="text-lg mb-1">⚙️</p>
          <p className="text-sm font-semibold">Settings</p>
          <p className="text-xs text-slate-400 mt-0.5">Manage profile and password</p>
        </Link>
      </div>
    </div>
  );
}
