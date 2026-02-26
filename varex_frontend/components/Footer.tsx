import Link from "next/link";
import Image from "next/image";

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
    href: "https://github.com/varextech",
    label: "GitHub",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M12 .3a12 12 0 0 0-3.79 23.4c.6.1.83-.26.83-.57v-2.18c-3.34.72-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.64 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .31.22.68.83.56A12 12 0 0 0 12 .3z" />
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
    <footer className="border-t border-slate-800 bg-slate-950">
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
            <p className="text-sm text-slate-400 leading-relaxed max-w-[200px]">
              Engineering & Talent Acceleration for DevSecOps, Cybersecurity, SAP SD, and AI Hiring.
            </p>

            {/* Social icons */}
            <div className="flex items-center gap-2 pt-2">
              {SOCIAL_LINKS.map((s) => (
                <a key={s.label}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={s.label}
                  className="flex items-center justify-center h-9 w-9 rounded-lg
                    border border-slate-700 text-slate-400
                    hover:border-sky-500/50 hover:text-sky-400 hover:bg-sky-500/10 transition-all duration-300">
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
                      className="text-sm text-slate-400 hover:text-sky-400 transition-colors duration-200"
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
            <Link href="/privacy" className="hover:text-sky-400 transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-sky-400 transition-colors">Terms</Link>
            <Link href="/refund" className="hover:text-sky-400 transition-colors">Refund</Link>
            <span>Bengaluru, India</span>
          </div>
        </div>

      </div>
    </footer>
  );
}
