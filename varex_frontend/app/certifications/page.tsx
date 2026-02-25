"use client";
import { useEffect, useState } from "react";
import { listCertifications, listAchievements } from "@/lib/api";
import type { Certification, Achievement } from "@/lib/types";

const DOMAIN_LABELS: Record<string, string> = {
  devops: "DevOps", security: "Security", cloud: "Cloud", sap: "SAP", ai: "AI", other: "Other"
};

export default function CertificationsPage() {
  const [certs, setCerts] = useState<Certification[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);

  useEffect(() => {
    listCertifications().then(setCerts);
    listAchievements().then(setAchievements);
  }, []);

  const grouped = certs.reduce<Record<string, Certification[]>>((acc, c) => {
    acc[c.domain] = acc[c.domain] ? [...acc[c.domain], c] : [c];
    return acc;
  }, {});

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-2xl font-semibold mb-1">Certifications & Achievements</h1>
        <p className="text-sm text-slate-300">Verified credentials and company milestones across DevOps, Security, SAP, and Cloud.</p>
      </header>

      {achievements.length > 0 && (
        <section>
          <h2 className="text-base font-semibold mb-4">🏆 Company Achievements</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {achievements.map((a) => (
              <div key={a.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-center">
                {a.metric && <p className="text-2xl font-bold text-sky-400 mb-1">{a.metric}</p>}
                <p className="text-xs font-semibold text-slate-100">{a.title}</p>
                <p className="text-[11px] text-slate-400 mt-1">{a.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {Object.entries(grouped).map(([domain, items]) => (
        <section key={domain}>
          <h2 className="text-base font-semibold mb-3">{DOMAIN_LABELS[domain] ?? domain} Certifications</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((c) => (
              <div key={c.id} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 text-lg flex-shrink-0">🎓</div>
                <div>
                  <p className="text-xs font-semibold text-slate-100">{c.title}</p>
                  <p className="text-[11px] text-slate-400">{c.issuing_body}</p>
                  {c.issued_date && <p className="text-[10px] text-slate-500 mt-0.5">{c.issued_date}</p>}
                  {c.credential_url && (
                    <a href={c.credential_url} target="_blank" rel="noopener"
                      className="text-[10px] text-sky-400 hover:text-sky-300">
                      Verify credential →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
