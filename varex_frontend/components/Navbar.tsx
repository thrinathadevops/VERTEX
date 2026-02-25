"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

// ── Navigation link definitions ───────────────────────────────────
const PRIMARY_LINKS = [
  { href: "/",            label: "Home"      },
  { href: "/services",    label: "Services"  },
  { href: "/hire",        label: "Hire"      },
  { href: "/portfolio",   label: "Portfolio" },
  { href: "/team",        label: "Team"      },
  { href: "/dashboard",   label: "Dashboard" },
];

const HAMBURGER_LINKS = [
  { section: "📚 Learnings", links: [
    { href: "/blog",              label: "All Posts"    },
    { href: "/blog/devops",       label: "DevOps"       },
    { href: "/blog/security",     label: "Security"     },
    { href: "/blog/sap",          label: "SAP SD"       },
    { href: "/blog/architecture", label: "Architecture" },
  ]},
  { section: "🚀 Company", links: [
    { href: "/portfolio",      label: "Projects"       },
    { href: "/certifications", label: "Certifications" },
    { href: "/team",           label: "Our Team"       },
  ]},
  { section: "🎓 Programs", links: [
    { href: "/workshops", label: "Workshops"        },
    { href: "/learnings", label: "Premium Learning" },
    { href: "/hire",      label: "Hire in 7 Days"   },
  ]},
  { section: "📞 Connect", links: [
    { href: "/contact", label: "Get Free Consultation" },
    { href: "/faq",     label: "FAQ"                   },
  ]},
];

export default function Navbar() {
  const pathname = usePathname();
  const router   = useRouter();
  const [user,     setUser]     = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setUser(getUserFromCookies());
    setMenuOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">

        {/* ── Logo ──────────────────────────────────────────────── */}
        <Link href="/" className="flex items-center gap-2 flex-shrink-0">
          <Image
            src="/varex-logo-enterprise.svg"
            alt="VAREX"
            width={140}
            height={36}
            priority
          />
        </Link>

        {/* ── Primary nav links (desktop) ───────────────────────── */}
        <nav className="hidden lg:flex items-center gap-1 text-xs">
          {PRIMARY_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-md px-2.5 py-1.5 transition ${
                pathname === link.href
                  ? "bg-slate-800 text-slate-50"
                  : "text-slate-300 hover:text-slate-50 hover:bg-slate-800/50"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* ── Right side: auth + hamburger ──────────────────────── */}
        <div className="flex items-center gap-2 text-xs">
          {user ? (
            <>
              <span className="hidden md:inline text-slate-400 text-[11px]">
                {user.email}
              </span>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] capitalize text-slate-200">
                {user.role.replace("_", " ")}
              </span>
              <button
                onClick={handleLogout}
                className="rounded-md border border-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:border-sky-500"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md border border-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:border-sky-500"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="hidden sm:inline rounded-md bg-sky-500 px-3 py-1 text-[11px] font-semibold text-white hover:bg-sky-400"
              >
                Get started
              </Link>
            </>
          )}

          {/* Hamburger button */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Open menu"
            className="ml-1 flex flex-col gap-[5px] p-1.5 rounded-md hover:bg-slate-800"
          >
            <span className={`block h-0.5 w-5 bg-slate-300 transition-transform ${menuOpen ? "rotate-45 translate-y-[7px]" : ""}`} />
            <span className={`block h-0.5 w-5 bg-slate-300 transition-opacity  ${menuOpen ? "opacity-0" : ""}`} />
            <span className={`block h-0.5 w-5 bg-slate-300 transition-transform ${menuOpen ? "-rotate-45 -translate-y-[7px]" : ""}`} />
          </button>
        </div>
      </div>

      {/* ── Hamburger dropdown ────────────────────────────────────── */}
      {menuOpen && (
        <div className="border-t border-slate-800 bg-slate-950/95 px-4 py-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {HAMBURGER_LINKS.map((group) => (
            <div key={group.section}>
              <p className="mb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                {group.section}
              </p>
              <ul className="space-y-1">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      onClick={() => setMenuOpen(false)}
                      className={`block rounded-md px-2 py-1.5 text-xs transition ${
                        pathname === link.href
                          ? "bg-sky-500/20 text-sky-300"
                          : "text-slate-300 hover:bg-slate-800 hover:text-slate-50"
                      }`}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {/* Mobile: show primary links too */}
          <div className="lg:hidden col-span-full border-t border-slate-800 pt-3 flex flex-wrap gap-2">
            {PRIMARY_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="rounded-md bg-slate-800 px-3 py-1 text-xs text-slate-200 hover:bg-slate-700"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}