"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getTeamMember } from "@/lib/api";
import type { TeamMember } from "@/lib/types";

export default function TeamMemberPage() {
  const { slug } = useParams<{ slug: string }>();
  const [member, setMember] = useState<TeamMember | null>(null);

  useEffect(() => {
    if (slug) getTeamMember(slug).then(setMember).catch(console.error);
  }, [slug]);

  if (!member) return <p className="text-sm text-slate-300">Loading profile...</p>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <div className="h-16 w-16 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-300 font-bold text-2xl">
          {member.name[0]}
        </div>
        <div>
          <h1 className="text-2xl font-semibold">{member.name}</h1>
          <p className="text-sm text-slate-400">{member.title}</p>
          <p className="text-xs text-slate-400">{member.years_experience} years experience</p>
        </div>
      </div>

      {member.bio && <p className="text-sm text-slate-300">{member.bio}</p>}

      <section className="grid gap-4 md:grid-cols-2">
        {member.specializations && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="text-xs font-semibold text-slate-200 mb-2">Specializations</h2>
            <ul className="space-y-1">
              {member.specializations.map((s) => (
                <li key={s} className="text-xs text-slate-300 flex items-center gap-1.5">
                  <span className="h-1 w-1 rounded-full bg-sky-400" />{s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {member.tools && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="text-xs font-semibold text-slate-200 mb-2">Tools & Tech</h2>
            <div className="flex flex-wrap gap-1">
              {member.tools.map((t) => (
                <span key={t} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-sky-300">{t}</span>
              ))}
            </div>
          </div>
        )}
      </section>

      {member.pricing && (
        <section className="rounded-xl border border-sky-700/50 bg-sky-950/40 p-4">
          <h2 className="text-sm font-semibold text-sky-100 mb-3">💰 Consulting Rates</h2>
          <ul className="space-y-1.5">
            {Object.entries(member.pricing).map(([service, rate]) => (
              <li key={service} className="flex items-center justify-between text-xs">
                <span className="text-slate-200 capitalize">{service.replace(/_/g, " ")}</span>
                <span className="font-semibold text-sky-200">₹{rate}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {member.available_for && (
        <div className="flex flex-wrap gap-2">
          {member.available_for.map((a) => (
            <span key={a} className="rounded-full border border-emerald-600/40 bg-emerald-900/30 px-2 py-0.5 text-[11px] text-emerald-200">
              Available for: {a}
            </span>
          ))}
          {member.available_from && (
            <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300">
              From: {member.available_from}
            </span>
          )}
        </div>
      )}

      {member.linkedin_url && (
        <a href={member.linkedin_url} target="_blank" rel="noopener"
          className="inline-block rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
          Connect on LinkedIn
        </a>
      )}
    </div>
  );
}
