"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const PRIMARY_LINKS = [
  { href: "/", label: "Home" },
  { href: "/services", label: "Services" },
  { href: "/hire", label: "Hire" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/team", label: "Team" },
  { href: "/dashboard", label: "Dashboard" },
];

const HAMBURGER_LINKS = [
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

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    setUser(getUserFromCookies());
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    router.push("/");
  };

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 ${scrolled
        ? "bg-slate-950/95 backdrop-blur-xl border-b border-slate-800 shadow-lg shadow-slate-950/50"
        : "bg-transparent border-b border-transparent"
      }`}>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">

        {/* ── Logo ──────────────────────────────────────────────── */}
        <Link href="/" className="flex items-center gap-2 flex-shrink-0 group">
          <Image
            src="/varex-logo-enterprise.svg"
            alt="VAREX"
            width={130}
            height={34}
            priority
            className="group-hover:opacity-90 transition-opacity"
          />
        </Link>

        {/* ── Primary nav links (desktop) ───────────────────────── */}
        <nav className="hidden lg:flex items-center gap-1">
          {PRIMARY_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`relative rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${pathname === link.href
                  ? "text-white"
                  : "text-slate-400 hover:text-white"
                }`}
            >
              {link.label}
              {pathname === link.href && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-lg bg-white/10"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </Link>
          ))}
        </nav>

        {/* ── Right side: auth + hamburger ──────────────────────── */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden md:inline text-slate-400 text-xs">
                {user.email}
              </span>
              <span className="rounded-full bg-sky-500/15 px-2.5 py-0.5 text-[11px] capitalize text-sky-300 font-semibold">
                {user.role.replace("_", " ")}
              </span>
              <button
                onClick={handleLogout}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-red-500/50 hover:text-red-400 transition-all"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden sm:inline rounded-lg border border-slate-700 px-4 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-500/50 hover:text-sky-400 transition-all"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-sky-500 hover:bg-sky-400 px-4 py-1.5 text-xs font-bold text-white shadow-md shadow-sky-500/20 transition-all"
              >
                Get Started
              </Link>
            </>
          )}

          {/* Hamburger button */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Open menu"
            className="ml-1 flex flex-col gap-[5px] p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <span className={`block h-0.5 w-5 rounded-full bg-slate-300 transition-all duration-300 ${menuOpen ? "rotate-45 translate-y-[7px]" : ""}`} />
            <span className={`block h-0.5 w-5 rounded-full bg-slate-300 transition-all duration-300 ${menuOpen ? "opacity-0 scale-0" : ""}`} />
            <span className={`block h-0.5 w-5 rounded-full bg-slate-300 transition-all duration-300 ${menuOpen ? "-rotate-45 -translate-y-[7px]" : ""}`} />
          </button>
        </div>
      </div>

      {/* ── Hamburger dropdown with animation ──────────────────── */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.25, 0.4, 0.25, 1] }}
            className="overflow-hidden border-t border-slate-800 bg-slate-950/98 backdrop-blur-xl"
          >
            <div className="px-4 py-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
              {HAMBURGER_LINKS.map((group, idx) => (
                <motion.div
                  key={group.section}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05, duration: 0.3 }}
                >
                  <p className="mb-3 text-xs font-bold text-sky-400 uppercase tracking-wider">
                    {group.section}
                  </p>
                  <ul className="space-y-1">
                    {group.links.map((link) => (
                      <li key={link.href}>
                        <Link
                          href={link.href}
                          onClick={() => setMenuOpen(false)}
                          className={`block rounded-lg px-3 py-2 text-sm transition-all ${pathname === link.href
                              ? "bg-sky-500/15 text-sky-300 font-medium"
                              : "text-slate-400 hover:bg-white/5 hover:text-white"
                            }`}
                        >
                          {link.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
              {/* Mobile: primary links */}
              <div className="lg:hidden col-span-full border-t border-slate-800 pt-4 flex flex-wrap gap-2">
                {PRIMARY_LINKS.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMenuOpen(false)}
                    className="rounded-lg bg-slate-800 hover:bg-slate-700 px-4 py-2 text-sm text-slate-200 transition-colors"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}