"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { listTeam } from "@/lib/api";
import type { TeamMember } from "@/lib/types";

export default function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);

  useEffect(() => { listTeam().then(setMembers); }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold mb-1">Core Engineers</h1>
        <p className="text-sm text-slate-300">Click any profile to see experience, certifications, and consulting rates.</p>
      </header>
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {members.map((m) => (
          <Link key={m.id} href={`/team/${m.slug}`}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 hover:border-sky-600/70 block">
            <div className="flex items-center gap-3 mb-3">
              {m.avatar_url ? (
                <img src={m.avatar_url} alt={m.name} className="h-12 w-12 rounded-full object-cover border border-slate-700" />
              ) : (
                <div className="h-12 w-12 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-300 font-bold text-lg">
                  {m.name[0]}
                </div>
              )}
              <div>
                <p className="text-sm font-semibold">{m.name}</p>
                <p className="text-xs text-slate-400">{m.title}</p>
              </div>
            </div>
            <p className="text-xs text-slate-300 mb-3 line-clamp-2">{m.bio}</p>
            {m.specializations && (
              <div className="flex flex-wrap gap-1">
                {m.specializations.slice(0, 3).map((s) => (
                  <span key={s} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-sky-300">{s}</span>
                ))}
              </div>
            )}
            <p className="mt-3 text-[11px] text-sky-400">View full profile & pricing →</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
