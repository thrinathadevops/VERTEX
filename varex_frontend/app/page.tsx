import Link from "next/link";
import Testimonials     from "@/components/Testimonials";
import NewsletterSignup from "@/components/NewsletterSignup";
import { PAGE_META }    from "@/lib/metadata";

export const metadata = PAGE_META.home;

export default function HomePage() {
  return (
    <div className="space-y-20">

      {/* ── Hero ──────────────────────────────────────────────── */}
      <div className="grid gap-10 lg:grid-cols-[3fr_2fr] items-center">
        <section>
          <span className="inline-flex items-center rounded-full border border-sky-500/40
            bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-200 mb-4">
            VAREX • Virtual Architecture, Resilience & Execution
          </span>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            Secure SaaS infrastructure for the next generation of builders.
          </h1>
          <p className="text-slate-300 mb-6 max-w-xl">
            VAREX gives teams a production-ready foundation: authentication, role-based access,
            and premium content delivery — backed by a resilient FastAPI core.
          </p>
          <div className="flex flex-wrap gap-3 mb-10">
            <Link href="/register"
              className="rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white
                shadow-lg shadow-sky-500/30 hover:bg-sky-400 transition">
              Get started
            </Link>
            <Link href="/dashboard"
              className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-medium
                text-slate-100 hover:border-sky-500/60 transition">
              View dashboard
            </Link>
          </div>
          <dl className="grid grid-cols-3 gap-4 text-xs text-slate-300 max-w-md">
            <div>
              <dt className="font-semibold text-slate-100">RBAC</dt>
              <dd>Guest, free, premium, and admin roles out of the box.</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-100">API-first</dt>
              <dd>FastAPI backend with JWT auth and clean architecture.</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-100">Ready for AI</dt>
              <dd>Pluggable interview module and premium insights.</dd>
            </div>
          </dl>
        </section>

        {/* Live signal card */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl shadow-sky-900/40">
          <h2 className="text-lg font-semibold mb-4">Live signal</h2>
          <div className="space-y-3 text-sm text-slate-300">
            <div className="flex items-center justify-between">
              <span>API status</span>
              <span className="inline-flex items-center gap-1 rounded-full
                bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Auth provider</span>
              <span className="text-slate-100">JWT • FastAPI</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Regions</span>
              <span className="text-slate-100">AWS ap-south-1</span>
            </div>
          </div>

          {/* Quick links */}
          <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-2 gap-2">
            {[
              { href: "/blog",       label: "Read blog"     },
              { href: "/portfolio",  label: "Case studies"  },
              { href: "/workshops",  label: "Workshops"     },
              { href: "/contact",    label: "Consultation"  },
            ].map((l) => (
              <Link key={l.href} href={l.href}
                className="rounded-lg border border-slate-700 px-3 py-2 text-[11px]
                  text-slate-300 hover:border-sky-500/60 hover:text-sky-300 transition text-center">
                {l.label}
              </Link>
            ))}
          </div>

          <p className="mt-4 text-xs text-slate-400">
            Sign in to see your dashboard, subscription, and premium learning paths.
          </p>
        </section>
      </div>

      {/* ── Services strip ────────────────────────────────────── */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: "⚙️", title: "DevSecOps",       desc: "CI/CD pipelines, Kubernetes, IaC, and SRE practices.",          href: "/services"  },
          { icon: "🛡",  title: "Cybersecurity",   desc: "Pen testing, threat modelling, and compliance frameworks.",     href: "/services"  },
          { icon: "📦", title: "SAP SD",           desc: "SD configuration, integration, and delivery management.",       href: "/services"  },
          { icon: "🤖", title: "AI Hiring",        desc: "Hire pre-vetted engineers in 7 days using AI screening.",       href: "/hire"      },
        ].map((s) => (
          <Link key={s.title} href={s.href}
            className="group rounded-2xl border border-slate-800 bg-slate-900/70 p-4
              hover:border-sky-600/60 transition space-y-2">
            <span className="text-2xl">{s.icon}</span>
            <p className="text-sm font-semibold text-slate-100 group-hover:text-sky-300 transition">
              {s.title}
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
          </Link>
        ))}
      </section>

      {/* ── Testimonials ──────────────────────────────────────── */}
      <Testimonials />

      {/* ── Newsletter ────────────────────────────────────────── */}
      <NewsletterSignup />

    </div>
  );
}