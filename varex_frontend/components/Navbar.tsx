"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";
import {
  Home,
  Briefcase,
  Award,
  Users,
  LayoutDashboard,
  LogIn,
  Rocket,
  Menu,
  X,
  FolderOpen,
} from "lucide-react";

/* ── Navigation data ─────────────────────────────────── */
const NAV_LINKS = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/services", label: "Services", Icon: Briefcase },
  { href: "/hire", label: "Hire", Icon: Award },
  { href: "/portfolio", label: "Portfolio", Icon: FolderOpen },
  { href: "/team", label: "Team", Icon: Users },
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
];

const MEGA_MENU = [
  {
    section: "Learnings", links: [
      { href: "/blog", label: "All Posts" },
      { href: "/blog/devops", label: "DevOps" },
      { href: "/blog/security", label: "Security" },
      { href: "/blog/sap", label: "SAP SD" },
      { href: "/blog/architecture", label: "Architecture" },
    ]
  },
  {
    section: "Company", links: [
      { href: "/portfolio", label: "Projects" },
      { href: "/certifications", label: "Certifications" },
      { href: "/team", label: "Our Team" },
    ]
  },
  {
    section: "Programs", links: [
      { href: "/workshops", label: "Workshops" },
      { href: "/learnings", label: "Premium Learning" },
      { href: "/hire", label: "Hire in 7 Days" },
    ]
  },
  {
    section: "Connect", links: [
      { href: "/contact", label: "Get Free Consultation" },
      { href: "/faq", label: "FAQ" },
    ]
  },
];

/* ── Component ───────────────────────────────────────── */
export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
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
    <header
      className="sticky top-0 z-50 border-b-[3px] border-cyan-400 shadow-[0_4px_30px_rgba(6,182,212,0.25)]"
      style={{ background: "linear-gradient(90deg, #0a1628 0%, #162044 50%, #0a1628 100%)" }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6"
        style={{ height: "68px" }}>

        {/* ═══ LEFT — Company Logo (PNG) ═══ */}
        <Link href="/" className="flex-shrink-0">
          <Image
            src="/varex-logo.png"
            alt="VAREX – Virtual Architecture, Resilience & Execution"
            width={160}
            height={45}
            priority
            className="object-contain"
            style={{ maxHeight: "45px", width: "auto" }}
          />
        </Link>

        {/* ═══ CENTER — Desktop Nav Links ═══ */}
        <nav className="hidden lg:flex items-center gap-1 ml-8">
          {NAV_LINKS.map(({ href, label, Icon }) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold
                  transition-all duration-200
                  ${active
                    ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/40"
                    : "text-slate-300 hover:text-white hover:bg-white/10"
                  }
                `}>
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* ═══ RIGHT — Auth + Hamburger ═══ */}
        <div className="flex items-center gap-3 ml-auto">
          {user ? (
            <>
              <span className="hidden md:inline text-slate-400 text-xs">{user.email}</span>
              <span className="rounded-full bg-cyan-500/20 border border-cyan-500/40
                               px-3 py-1 text-xs capitalize text-cyan-300 font-semibold">
                {user.role.replace("_", " ")}
              </span>
              <button onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border-2 border-slate-600
                           hover:border-red-500 px-4 py-2 text-sm font-semibold text-slate-200
                           hover:text-red-400 hover:bg-red-500/10 transition-all duration-200">
                <LogIn className="w-4 h-4" /> Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login"
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border-2
                           border-cyan-400/60 hover:border-cyan-300 px-4 py-2 text-sm font-semibold
                           text-slate-200 hover:text-cyan-300 hover:bg-cyan-500/10 transition-all duration-200">
                <LogIn className="w-4 h-4" /> Sign in
              </Link>
              <Link href="/register"
                className="inline-flex items-center gap-1.5 rounded-lg px-5 py-2 text-sm font-bold
                           text-white shadow-lg shadow-cyan-500/40 transition-all duration-200
                           hover:shadow-cyan-400/50"
                style={{ background: "linear-gradient(135deg, #06b6d4, #3b82f6)" }}>
                <Rocket className="w-4 h-4" /> Get Started
              </Link>
            </>
          )}

          {/* Hamburger */}
          <button onClick={() => setMenuOpen(v => !v)} aria-label="Toggle menu"
            className="ml-2 p-2 rounded-lg hover:bg-cyan-500/20 transition-colors duration-200">
            {menuOpen
              ? <X className="w-5 h-5 text-cyan-400" />
              : <Menu className="w-5 h-5 text-cyan-400" />}
          </button>
        </div>
      </div>

      {/* ═══ Mega-menu dropdown (pure CSS transition) ═══ */}
      <div className={`
        overflow-hidden transition-all duration-300 ease-in-out border-t-2 border-cyan-400/30
        ${menuOpen ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0 border-t-0"}
      `}
        style={{ background: "linear-gradient(180deg, #0d1a30ee, #162044ee)" }}>
        <div className="px-6 py-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
          {MEGA_MENU.map((group) => (
            <div key={group.section}>
              <p className="mb-3 text-xs font-bold text-cyan-400 uppercase tracking-widest">
                {group.section}
              </p>
              <ul className="space-y-1">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} onClick={() => setMenuOpen(false)}
                      className={`block rounded-lg px-3 py-2 text-sm transition-all duration-200
                        ${pathname === link.href
                          ? "bg-cyan-500/15 text-cyan-300 font-medium"
                          : "text-slate-400 hover:bg-white/5 hover:text-white"
                        }`}>
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Mobile: primary links */}
          <div className="lg:hidden col-span-full border-t border-slate-700 pt-4 flex flex-wrap gap-2">
            {NAV_LINKS.map(({ href, label, Icon }) => (
              <Link key={href} href={href} onClick={() => setMenuOpen(false)}
                className="flex items-center gap-2 rounded-lg bg-slate-800 hover:bg-slate-700
                           px-4 py-2 text-sm text-slate-200 transition-colors duration-200">
                <Icon className="w-4 h-4" /> {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}