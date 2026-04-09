import Link from "next/link";
import Image from "next/image";
import GithubShortcut from "@/components/GithubShortcut";

const FOOTER_LINKS = {
  "Services": [
    { href: "/services", label: "What We Do" },
    { href: "/hire", label: "Hire in 7 Days" },
    { href: "/workshops", label: "Workshops" },
    { href: "/portfolio", label: "Portfolio" },
    { href: "/contact", label: "Free Consultation" },
  ],
  "Learn": [
    { href: "/blog", label: "All Posts" },
    { href: "/blog/devops", label: "DevOps" },
    { href: "/blog/security", label: "Security" },
    { href: "/blog/sap", label: "SAP SD" },
    { href: "/blog/architecture", label: "Architecture" },
    { href: "/learnings", label: "Premium Learning" },
  ],
  "Company": [
    { href: "/team", label: "Our Team" },
    { href: "/certifications", label: "Certifications" },
    { href: "/faq", label: "FAQ" },
    { href: "/pricing", label: "Pricing" },
  ],
  "Legal": [
    { href: "/privacy", label: "Privacy Policy" },
    { href: "/terms", label: "Terms of Service" },
    { href: "/refund", label: "Refund Policy" },
  ],
};

const SOCIAL_LINKS = [
  {
    href: "https://www.linkedin.com/company/varextech",
    label: "LinkedIn",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.37V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.59 0 4.26 2.37 4.26 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zm1.78 13.02H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46C23.2 24 24 23.23 24 22.28V1.72C24 .77 23.2 0 22.23 0z" />
      </svg>
    ),
  },
  {
    href: "https://www.upwork.com/ag/varextech",
    label: "Upwork",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M18.56 14.29c-1.38 0-2.67-.57-3.67-1.48l.27-1.28.01-.07c.24-1.36 1-3.64 3.39-3.64a3.24 3.24 0 0 1 3.24 3.24 3.24 3.24 0 0 1-3.24 3.23zm0-8.54c-2.9 0-5.06 1.88-5.93 4.96-.87-1.6-1.54-3.52-1.93-5.14H8.15v6.22a2.28 2.28 0 0 1-2.28 2.28 2.28 2.28 0 0 1-2.28-2.28V5.57H1.13v6.22a4.74 4.74 0 0 0 4.74 4.74 4.74 4.74 0 0 0 4.74-4.74v-1.04c.38 1.05.88 2.12 1.5 3.07L10.9 19h2.55l.95-4.37c1.13.82 2.5 1.32 3.9 1.32a5.7 5.7 0 0 0 5.7-5.7 5.7 5.7 0 0 0-5.44-5.5z" />
      </svg>
    ),
  },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative overflow-hidden border-t border-slate-800 bg-slate-950">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-0 top-0 h-48 w-72 bg-emerald-400/10 blur-[100px]" />
        <div className="absolute right-0 top-8 h-48 w-72 bg-cyan-400/10 blur-[100px]" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />
        <svg className="absolute inset-0 h-full w-full opacity-30 footer-signal" viewBox="0 0 1440 420" fill="none" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 112C146 112 186 168 298 168C410 168 448 120 576 120C696 120 736 192 868 192C1012 192 1084 128 1204 128C1300 128 1362 156 1440 156" stroke="rgba(56,189,248,0.18)" strokeWidth="1.2" strokeDasharray="7 10" />
          <path d="M86 290C214 290 284 240 406 240C532 240 596 302 722 302C850 302 926 258 1042 258C1162 258 1260 316 1440 316" stroke="rgba(16,185,129,0.16)" strokeWidth="1.1" strokeDasharray="6 12" />
          <path d="M128 82H284L368 120H576L648 90H820L868 192L1020 192L1122 128H1304" stroke="rgba(190,242,100,0.12)" strokeWidth="1" strokeDasharray="8 12" />
          <circle cx="576" cy="120" r="4" fill="rgba(56,189,248,0.55)" />
          <circle cx="868" cy="192" r="4" fill="rgba(16,185,129,0.55)" />
          <circle cx="722" cy="302" r="3.5" fill="rgba(99,102,241,0.45)" />
          <circle cx="1122" cy="128" r="3.5" fill="rgba(190,242,100,0.45)" />
        </svg>
      </div>
      <div className="mx-auto max-w-6xl px-4 py-16">
        {/* ── Top: Brand + Links grid ───────────────────────── */}
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-5">

          {/* Brand column */}
          <div className="lg:col-span-1 space-y-4">
            <Link href="/" className="block">
              <Image
                src="/varex-logo-enterprise.svg"
                alt="VAREX"
                width={140}
                height={40}
                className="object-contain"
                style={{ maxHeight: "40px", width: "auto" }}
              />
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed max-w-[220px]">
              Engineering & Talent Acceleration for DevSecOps, Cybersecurity, SAP SD, and AI Hiring.
            </p>
            <div className="rounded-2xl border border-emerald-400/10 bg-slate-900/55 px-4 py-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-emerald-200/65">Command Stack</p>
              <p className="mt-2 text-sm text-slate-300">Architecture, hardening, delivery automation, and technical talent execution in one operating layer.</p>
            </div>

            {/* Social icons */}
            <div className="flex items-center gap-2 pt-2">
              <GithubShortcut />
              {SOCIAL_LINKS.map((s) => (
                <a key={s.label}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={s.label}
                  className="flex items-center justify-center h-11 w-11 rounded-lg
                    border border-slate-700 text-slate-400
                    hover:border-sky-500/50 hover:text-sky-400 hover:bg-sky-500/10 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400">
                  {s.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <p className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-300">
                {section}
              </p>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-slate-400 hover:text-sky-400 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 rounded-sm"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* ── Divider ───────────────────────────────────────── */}
        <div className="mt-12 border-t border-slate-800 pt-8
          flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-slate-500">
            © {year} VAREX Technologies. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link href="/privacy" className="hover:text-sky-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 rounded-sm">Privacy</Link>
            <Link href="/terms" className="hover:text-sky-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 rounded-sm">Terms</Link>
            <Link href="/refund" className="hover:text-sky-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 rounded-sm">Refund</Link>
            <span>Bengaluru, India</span>
          </div>
        </div>

      </div>
    </footer>
  );
}
