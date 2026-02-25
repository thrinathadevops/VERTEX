// PATH: varex-frontend/app/dashboard/settings/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/lib/api";
import AvatarUpload from "@/components/AvatarUpload";
import ProtectedRoute from "@/components/ProtectedRoute";
import type { User } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function SettingsInner() {
  const router = useRouter();
  const [user,    setUser]    = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab,     setTab]     = useState<"profile" | "password" | "subscription">("profile");

  // Profile form
  const [name,    setName]    = useState("");
  const [saving,  setSaving]  = useState(false);
  const [msg,     setMsg]     = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Password form
  const [oldPw,   setOldPw]   = useState("");
  const [newPw,   setNewPw]   = useState("");
  const [confPw,  setConfPw]  = useState("");
  const [pwMsg,   setPwMsg]   = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [pwSaving,setPwSaving]= useState(false);

  useEffect(() => {
    getMe()
      .then((me) => { setUser(me); setName(me.name); })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, []);

  const getToken = () =>
    document.cookie.match(/access_token=([^;]+)/)?.[1] ?? "";

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSaving(true); setMsg(null);
    try {
      const res = await fetch(`${API}/api/v1/users/${user.id}`, {
        method:  "PATCH",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body:    JSON.stringify({ name }),
      });
      if (!res.ok) throw new Error(await res.text());
      setUser((u) => u ? { ...u, name } : u);
      setMsg({ type: "success", text: "Profile updated successfully." });
    } catch {
      setMsg({ type: "error", text: "Failed to update profile. Try again." });
    } finally { setSaving(false); }
  };

  const handleAvatarUpload = async (publicUrl: string, s3Key: string) => {
    if (!user) return;
    await fetch(`${API}/api/v1/users/${user.id}`, {
      method:  "PATCH",
      headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
      body:    JSON.stringify({ avatar_url: publicUrl }),
    });
    setUser((u) => u ? { ...u, avatar_url: publicUrl } : u);
    setMsg({ type: "success", text: "Avatar updated." });
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confPw) { setPwMsg({ type: "error", text: "Passwords do not match." }); return; }
    if (newPw.length < 8)  { setPwMsg({ type: "error", text: "Password must be at least 8 characters." }); return; }
    setPwSaving(true); setPwMsg(null);
    try {
      const res = await fetch(`${API}/api/v1/auth/change-password`, {
        method:  "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body:    JSON.stringify({ old_password: oldPw, new_password: newPw }),
      });
      if (!res.ok) throw new Error(await res.text());
      setPwMsg({ type: "success", text: "Password changed successfully." });
      setOldPw(""); setNewPw(""); setConfPw("");
    } catch {
      setPwMsg({ type: "error", text: "Incorrect current password." });
    } finally { setPwSaving(false); }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );
  if (!user) return null;

  const TABS = [
    { key: "profile",      label: "Profile"      },
    { key: "password",     label: "Password"     },
    { key: "subscription", label: "Subscription" },
  ] as const;

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <header>
        <h1 className="text-xl font-bold">Account Settings</h1>
        <p className="text-xs text-slate-400 mt-0.5">{user.email}</p>
      </header>

      {/* Tab nav */}
      <nav className="flex gap-1 border-b border-slate-800">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-xs font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-sky-500 text-sky-300"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}>{t.label}</button>
        ))}
      </nav>

      {/* Profile tab */}
      {tab === "profile" && (
        <div className="space-y-6">
          <AvatarUpload
            currentUrl={user.avatar_url}
            name={user.name}
            onUpload={handleAvatarUpload}
          />
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Full name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2
                  text-sm text-slate-100 focus:border-sky-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
              <input value={user.email} disabled
                className="w-full rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2
                  text-sm text-slate-500 cursor-not-allowed" />
              <p className="mt-1 text-[11px] text-slate-500">Email cannot be changed.</p>
            </div>
            {msg && (
              <p className={`text-[11px] rounded-md px-3 py-2 ${
                msg.type === "success" ? "bg-emerald-950/50 text-emerald-300" : "bg-red-950/50 text-red-300"
              }`}>{msg.text}</p>
            )}
            <button type="submit" disabled={saving}
              className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold
                text-white hover:bg-sky-400 disabled:opacity-60 transition">
              {saving ? "Saving..." : "Save changes"}
            </button>
          </form>
        </div>
      )}

      {/* Password tab */}
      {tab === "password" && (
        <form onSubmit={handleChangePassword} className="space-y-4">
          {[
            { label: "Current password",  value: oldPw,  setter: setOldPw  },
            { label: "New password",      value: newPw,  setter: setNewPw  },
            { label: "Confirm password",  value: confPw, setter: setConfPw },
          ].map((f) => (
            <div key={f.label}>
              <label className="block text-xs font-medium text-slate-300 mb-1">{f.label}</label>
              <input type="password" value={f.value} onChange={(e) => f.setter(e.target.value)} required
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2
                  text-sm text-slate-100 focus:border-sky-500 focus:outline-none" />
            </div>
          ))}
          {pwMsg && (
            <p className={`text-[11px] rounded-md px-3 py-2 ${
              pwMsg.type === "success" ? "bg-emerald-950/50 text-emerald-300" : "bg-red-950/50 text-red-300"
            }`}>{pwMsg.text}</p>
          )}
          <button type="submit" disabled={pwSaving}
            className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold
              text-white hover:bg-sky-400 disabled:opacity-60 transition">
            {pwSaving ? "Changing..." : "Change password"}
          </button>
        </form>
      )}

      {/* Subscription tab */}
      {tab === "subscription" && (
        <div className="space-y-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold">Current plan</p>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${
                user.role === "premium"    ? "bg-amber-500/20 text-amber-300"  :
                user.role === "enterprise" ? "bg-purple-500/20 text-purple-300":
                "bg-slate-700 text-slate-300"
              }`}>{user.role.replace("_", " ")}</span>
            </div>
            <p className="text-xs text-slate-400">
              {user.role === "free_user"
                ? "Upgrade to Premium to access all modules, workshop recordings, and architecture deep dives."
                : "Manage your subscription, view billing history, or contact support."}
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {user.role === "free_user" && (
              <a href="/pricing"
                className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold
                  text-white hover:bg-sky-400 transition text-center">
                Upgrade to Premium
              </a>
            )}
            <a href="/contact?service=billing"
              className="w-full rounded-lg border border-slate-700 py-2.5 text-sm
                text-slate-200 hover:border-sky-500/60 transition text-center">
              Contact billing support
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  return <ProtectedRoute><SettingsInner /></ProtectedRoute>;
}
