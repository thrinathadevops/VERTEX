"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/lib/api";
import type { User } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function adminFetch<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

async function adminPatch(path: string, body: object, token: string) {
  await fetch(`${API}/api/v1${path}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

interface AdminUser { id: string; name: string; email: string; role: string; is_active: boolean; created_at: string; }
interface AdminLead { id: string; name: string; email: string; company?: string; service_interest: string; status: string; created_at: string; }
type Tab = "overview" | "users" | "leads" | "content";

const ROLE_COLORS: Record<string, string> = {
  admin:      "bg-purple-500/20 text-purple-300",
  enterprise: "bg-amber-500/20  text-amber-300",
  premium:    "bg-sky-500/20    text-sky-300",
  free_user:  "bg-slate-700     text-slate-300",
};

const LEAD_STATUS_COLORS: Record<string, string> = {
  new:       "bg-emerald-500/20 text-emerald-300",
  contacted: "bg-sky-500/20     text-sky-300",
  qualified: "bg-amber-500/20   text-amber-300",
  converted: "bg-purple-500/20  text-purple-300",
  rejected:  "bg-red-500/20     text-red-300",
};

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-1">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">{label}</p>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-slate-50">{value}</p>
    </div>
  );
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [user,    setUser]    = useState<User | null>(null);
  const [tab,     setTab]     = useState<Tab>("overview");
  const [users,   setUsers]   = useState<AdminUser[]>([]);
  const [leads,   setLeads]   = useState<AdminLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [token,   setToken]   = useState("");

  useEffect(() => {
    const t = document.cookie.match(/access_token=([^;]+)/)?.[1] ?? "";
    setToken(t);
    getMe()
      .then((me) => {
        if (me.role !== "admin") { router.replace("/dashboard"); return; }
        setUser(me);
        Promise.all([
          adminFetch<AdminUser[]>("/users", t),
          adminFetch<AdminLead[]>("/leads", t),
        ]).then(([u, l]) => { setUsers(u); setLeads(l); });
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, []);

  const handleLeadStatus = async (id: string, status: string) => {
    await adminPatch(`/leads/${id}/status`, { status }, token);
    setLeads((ls) => ls.map((l) => l.id === id ? { ...l, status } : l));
  };

  const handleToggleUser = async (id: string, is_active: boolean) => {
    await adminPatch(`/users/${id}`, { is_active: !is_active }, token);
    setUsers((us) => us.map((u) => u.id === id ? { ...u, is_active: !is_active } : u));
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );
  if (!user) return null;

  const TABS: { key: Tab; label: string; icon: string }[] = [
    { key: "overview", label: "Overview", icon: "📊" },
    { key: "users",    label: "Users",    icon: "👥" },
    { key: "leads",    label: "Leads",    icon: "📥" },
    { key: "content",  label: "Content",  icon: "📝" },
  ];

  const premiumCount    = users.filter((u) => u.role === "premium").length;
  const enterpriseCount = users.filter((u) => u.role === "enterprise").length;
  const newLeads        = leads.filter((l) => l.status === "new").length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Admin Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">Signed in as {user.email}</p>
        </div>
        <span className="rounded-full bg-purple-500/20 px-3 py-1 text-xs font-semibold text-purple-300">Admin</span>
      </header>

      <nav className="flex gap-1 border-b border-slate-800">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-2 text-xs font-medium transition border-b-2 -mb-px ${
              tab === t.key ? "border-sky-500 text-sky-300" : "border-transparent text-slate-400 hover:text-slate-200"
            }`}>
            {t.icon} {t.label}
          </button>
        ))}
      </nav>

      {/* OVERVIEW */}
      {tab === "overview" && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Users"        value={users.length}    icon="👥" />
            <StatCard label="Premium"            value={premiumCount}    icon="⭐" />
            <StatCard label="Enterprise Clients" value={enterpriseCount} icon="🏢" />
            <StatCard label="New Leads"          value={newLeads}        icon="📥" />
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-800 flex justify-between items-center">
              <p className="text-xs font-semibold">Recent Leads</p>
              <button onClick={() => setTab("leads")} className="text-[11px] text-sky-400 hover:text-sky-300">View all →</button>
            </div>
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-800 text-left">
                {["Name","Service","Status","Date"].map((h) => (
                  <th key={h} className="px-4 py-2 text-slate-400 font-medium">{h}</th>
                ))}
              </tr></thead>
              <tbody className="divide-y divide-slate-800/50">
                {leads.slice(0,5).map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-2.5 text-slate-200">{l.name}</td>
                    <td className="px-4 py-2.5 text-slate-300">{l.service_interest}</td>
                    <td className="px-4 py-2.5">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${LEAD_STATUS_COLORS[l.status] ?? "bg-slate-700 text-slate-300"}`}>{l.status}</span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400">{new Date(l.created_at).toLocaleDateString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* USERS */}
      {tab === "users" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800">
            <p className="text-xs font-semibold">All Users ({users.length})</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-800 text-left">
                {["Name","Email","Role","Joined","Status","Action"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-slate-400 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr></thead>
              <tbody className="divide-y divide-slate-800/50">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-2.5 text-slate-200 whitespace-nowrap">{u.name}</td>
                    <td className="px-4 py-2.5 text-slate-400">{u.email}</td>
                    <td className="px-4 py-2.5">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${ROLE_COLORS[u.role] ?? "bg-slate-700 text-slate-300"}`}>
                        {u.role.replace("_"," ")}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">{new Date(u.created_at).toLocaleDateString("en-IN")}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] font-medium ${u.is_active ? "text-emerald-400" : "text-red-400"}`}>
                        {u.is_active ? "Active" : "Suspended"}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      {u.role !== "admin" && (
                        <button onClick={() => handleToggleUser(u.id, u.is_active)}
                          className={`rounded px-2 py-1 text-[10px] font-medium transition ${
                            u.is_active ? "bg-red-500/20 text-red-300 hover:bg-red-500/30" : "bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30"
                          }`}>
                          {u.is_active ? "Suspend" : "Activate"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* LEADS */}
      {tab === "leads" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800">
            <p className="text-xs font-semibold">Consultation Leads ({leads.length})</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-800 text-left">
                {["Name","Email","Company","Service","Status","Date","Update"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-slate-400 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr></thead>
              <tbody className="divide-y divide-slate-800/50">
                {leads.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-2.5 text-slate-200 whitespace-nowrap">{l.name}</td>
                    <td className="px-4 py-2.5 text-slate-400">{l.email}</td>
                    <td className="px-4 py-2.5 text-slate-400">{l.company ?? "—"}</td>
                    <td className="px-4 py-2.5 text-slate-300 whitespace-nowrap">{l.service_interest}</td>
                    <td className="px-4 py-2.5">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${LEAD_STATUS_COLORS[l.status] ?? "bg-slate-700 text-slate-300"}`}>
                        {l.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">{new Date(l.created_at).toLocaleDateString("en-IN")}</td>
                    <td className="px-4 py-2.5">
                      <select value={l.status} onChange={(e) => handleLeadStatus(l.id, e.target.value)}
                        className="rounded bg-slate-800 border border-slate-700 px-2 py-1 text-[10px] text-slate-200 focus:border-sky-500 focus:outline-none">
                        {["new","contacted","qualified","converted","rejected"].map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CONTENT */}
      {tab === "content" && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { label: "Blog Posts",     href: "/blog",          icon: "📝", desc: "All blog content"        },
            { label: "Portfolio",      href: "/portfolio",     icon: "🗂", desc: "Project case studies"    },
            { label: "Team Members",   href: "/team",          icon: "👤", desc: "Profiles & pricing"      },
            { label: "Certifications", href: "/certifications",icon: "🏅", desc: "Certs & achievements"    },
            { label: "Workshops",      href: "/workshops",     icon: "🎓", desc: "Sessions & registrations"},
            { label: "FAQs",           href: "/faq",           icon: "❓", desc: "FAQ entries"             },
          ].map((item) => (
            <a key={item.label} href={item.href}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-600/70 transition space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-lg">{item.icon}</span>
                <p className="text-sm font-semibold text-slate-100">{item.label}</p>
              </div>
              <p className="text-xs text-slate-400">{item.desc}</p>
              <p className="text-[11px] text-sky-400">Manage →</p>
            </a>
          ))}
        </div>
      )}

    </div>
  );
}
