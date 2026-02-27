import Link from "next/link";

const steps = [
  {
    step: "01", title: "AI Screening",
    points: ["Resume parsing & ATS scan","Tool-based question generator","Scenario-based MCQ","Live coding evaluation","Scorecard generation"],
  },
  {
    step: "02", title: "Expert Interview Round",
    points: ["Conducted by VAREX principal architect","Real-world scenario questioning","Architecture design task","Performance & security review","Detailed evaluation report"],
  },
  {
    step: "03", title: "Client Selection",
    points: ["Only shortlisted elite engineers","Reduce 70% screening time","Reduce bad hire risk","Offer & onboarding support","7-day delivery guarantee"],
  },
];

export default function HirePage() {
  return (
    <div className="space-y-12">
      <header className="text-center">
        <span className="inline-block rounded-full bg-amber-500/20 px-3 py-1 text-xs text-amber-200 mb-3">
          VAREX Technical Talent Engine
        </span>
        <h1 className="text-3xl font-bold mb-3">
          We deliver production-ready engineers,<br className="hidden sm:block" /> not resumes.
        </h1>
        <p className="text-slate-300 max-w-xl mx-auto text-sm mb-6">
          AI-powered screening + expert validation = pre-vetted DevOps, Security & SAP specialists in 7 days.
        </p>
        <Link href="/contact?service=ai_hiring"
          className="inline-block rounded-lg bg-sky-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 hover:bg-sky-400">
          Start Hiring Now
        </Link>
        <div className="mt-3">
          <Link href="/ai-interview"
            className="inline-block rounded-lg border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-200 hover:border-sky-500 hover:text-white">
            Launch AI Interview App
          </Link>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-3">
        {steps.map((s) => (
          <div key={s.step} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <span className="text-3xl font-bold text-sky-500/30">{s.step}</span>
            <h2 className="text-base font-semibold mt-2 mb-3">{s.title}</h2>
            <ul className="space-y-1.5">
              {s.points.map((p) => (
                <li key={p} className="flex items-start gap-2 text-xs text-slate-300">
                  <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-sky-400 flex-shrink-0" />{p}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <h2 className="text-base font-semibold mb-4 text-center">Engagement Pricing</h2>
        <div className="grid gap-4 sm:grid-cols-3 text-center text-sm">
          <div className="rounded-xl border border-slate-700 p-4">
            <p className="text-xs text-slate-400 mb-1">Commission model</p>
            <p className="text-xl font-bold text-sky-400">8–15%</p>
            <p className="text-xs text-slate-300">of annual CTC per hire</p>
          </div>
          <div className="rounded-xl border border-sky-700/50 bg-sky-950/30 p-4">
            <p className="text-xs text-slate-400 mb-1">Flat fee model</p>
            <p className="text-xl font-bold text-sky-400">₹50,000</p>
            <p className="text-xs text-slate-300">per successful hire</p>
          </div>
          <div className="rounded-xl border border-slate-700 p-4">
            <p className="text-xs text-slate-400 mb-1">Delivery SLA</p>
            <p className="text-xl font-bold text-sky-400">7 Days</p>
            <p className="text-xs text-slate-300">from JD submission to shortlist</p>
          </div>
        </div>
      </section>
    </div>
  );
}
