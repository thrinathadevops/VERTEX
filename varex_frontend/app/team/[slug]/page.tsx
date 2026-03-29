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
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="grid md:grid-cols-[1fr_2fr] lg:grid-cols-[380px_1fr] gap-8 lg:gap-12 items-start">
        
        {/* LEFT COLUMN: Image & Quick Connect */}
        <div className="sticky top-24 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 flex flex-col items-center text-center shadow-xl shadow-sky-900/10 backdrop-blur-sm">
          <div className="relative w-48 h-48 mb-6 rounded-full p-1 bg-gradient-to-tr from-sky-500/30 to-indigo-500/30">
            <div className="w-full h-full rounded-full overflow-hidden border-2 border-slate-900 bg-slate-800 flex items-center justify-center">
              {member.avatar_url ? (
                <img src={member.avatar_url} alt={member.name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-sky-300 font-bold text-6xl">{member.name[0]}</span>
              )}
            </div>
          </div>
          
          <h1 className="text-2xl font-bold text-white leading-tight mb-2">{member.name}</h1>
          <p className="text-sm font-semibold text-sky-400 mb-1">{member.title}</p>
          <p className="text-xs text-slate-400 mb-6">{member.years_experience ? `${member.years_experience} years enterprise experience` : "Senior Consultant"}</p>

          {member.linkedin_url && (
            <a href={member.linkedin_url} target="_blank" rel="noopener" className="w-full flex justify-center items-center gap-2 rounded-xl bg-sky-500 hover:bg-sky-400 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-500/20 transition-all hover:-translate-y-0.5">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              Connect on LinkedIn
            </a>
          )}
        </div>

        {/* RIGHT COLUMN: Bio, Skills & Certs */}
        <div className="space-y-8">
          
          {/* Bio Section */}
          <section className="bg-slate-900/40 rounded-3xl border border-slate-800/50 p-6 sm:p-8">
            <h2 className="text-sm font-bold tracking-widest text-slate-500 uppercase flex items-center gap-2 mb-4">
              <span className="w-4 h-px bg-slate-500 inline-block"></span> About
            </h2>
            <p className="text-slate-300 leading-relaxed text-[15px]">
              {member.bio || "No biography provided."}
            </p>
          </section>

          {/* Grids for Skills/Certs */}
          <section className="grid gap-6 md:grid-cols-2">
            
            {member.specializations && member.specializations.length > 0 && (
              <div className="rounded-3xl border border-slate-800/50 bg-slate-900/40 p-6">
                <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-4">Core Competencies</h2>
                <ul className="space-y-3">
                  {member.specializations.map((s) => (
                    <li key={s} className="text-[13px] font-medium text-slate-200 flex items-start gap-2">
                      <span className="h-4 w-4 rounded-full bg-sky-500/10 text-sky-400 flex items-center justify-center shrink-0 mt-0.5">✦</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {member.tools && member.tools.length > 0 && (
              <div className="rounded-3xl border border-slate-800/50 bg-slate-900/40 p-6">
                <h2 className="text-sm font-bold tracking-widest text-indigo-400 uppercase mb-4">Tech Stack & Tools</h2>
                <div className="flex flex-wrap gap-2">
                  {member.tools.map((t) => (
                    <span key={t} className="rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-semibold text-indigo-300">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {member.certifications && member.certifications.length > 0 && (
              <div className="md:col-span-2 rounded-3xl border border-emerald-900/30 bg-emerald-950/10 p-6">
                 <h2 className="text-sm font-bold tracking-widest text-emerald-500 uppercase mb-4">Certifications</h2>
                 <div className="flex flex-wrap gap-3">
                    {member.certifications.map((cert) => (
                      <span key={cert} className="inline-flex items-center gap-2 rounded-xl bg-emerald-900/20 border border-emerald-800/50 px-3 py-2 text-xs font-semibold text-emerald-300">
                        🏆 {cert}
                      </span>
                    ))}
                 </div>
              </div>
            )}

          </section>

          {/* Availability & Rates */}
          {(member.pricing || member.available_for) && (
            <section className="rounded-3xl border border-sky-800/30 bg-sky-950/20 p-6 sm:p-8">
              {member.available_for && (
                <div className="mb-6">
                  <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-4">Availability</h2>
                  <div className="flex flex-wrap gap-2">
                    {member.available_for.map((a) => (
                      <span key={a} className="rounded-full border border-sky-600/40 bg-sky-900/30 px-3 py-1 text-xs font-medium text-sky-200">
                        {a}
                      </span>
                    ))}
                    {member.available_from && (
                      <span className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-300">
                        From: {member.available_from}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {member.pricing && (
                <div>
                  <h2 className="text-sm font-bold tracking-widest text-slate-400 uppercase mb-4">Consulting Rates</h2>
                  <ul className="grid sm:grid-cols-2 gap-3">
                    {Object.entries(member.pricing).map(([service, rate]) => (
                      <li key={service} className="flex flex-col rounded-xl bg-slate-900/50 p-3 border border-slate-800">
                        <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider mb-1">{service.replace(/_/g, " ")}</span>
                        <span className="font-extrabold text-sky-300 text-lg">₹{rate.toLocaleString()} <span className="text-xs font-medium text-slate-500">/hr</span></span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}

        </div>
      </div>
    </div>
  );
}
