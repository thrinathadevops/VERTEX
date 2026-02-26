"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogIn, Rocket, Menu, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const NAV_LINKS = [
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
    <header className="sticky top-0 z-50 bg-[#0B1120] border-b-2 border-sky-500/60 shadow-lg shadow-sky-900/20">
      {/* 
        Main header bar
        Height: ~60px (≈15mm on standard screen) 
        Layout: Logo (left) | Nav links (center) | Auth buttons (right)
      */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 h-[60px]">

        {/* ═══ LEFT: Company Logo ═══ */}
        <Link href="/" className="flex items-center gap-2 flex-shrink-0">
          <Image
            src="/varex-logo-enterprise.svg"
            alt="VAREX"
            width={130}
            height={34}
            priority
          />
        </Link>

        {/* ═══ CENTER: Navigation Links (Desktop) ═══ */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${isActive
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/30"
                    : "text-slate-300 hover:text-white hover:bg-white/10"
                  }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* ═══ RIGHT: Auth Buttons + Hamburger ═══ */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden md:inline text-slate-400 text-xs">
                {user.email}
              </span>
              <span className="rounded-full bg-sky-500/20 px-3 py-1 text-xs capitalize text-sky-300 font-semibold border border-sky-500/30">
                {user.role.replace("_", " ")}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 hover:border-red-500/50 hover:text-red-400 transition-all"
              >
                <LogIn className="w-4 h-4" />
                Sign out
              </button>
            </>
          ) : (
            <>
              {/* Sign In button with icon */}
              <Link
                href="/login"
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-slate-600 hover:border-sky-400 px-4 py-2 text-sm font-semibold text-slate-200 hover:text-sky-400 transition-all"
              >
                <LogIn className="w-4 h-4" />
                Sign in
              </Link>

              {/* Get Started button with icon */}
              <Link
                href="/register"
                className="inline-flex items-center gap-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 px-5 py-2 text-sm font-bold text-white transition-all shadow-md shadow-sky-500/30 hover:shadow-sky-400/40"
              >
                <Rocket className="w-4 h-4" />
                Get Started
              </Link>
            </>
          )}

          {/* Hamburger / More Menu button */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Open menu"
            className="ml-1 p-2 rounded-lg hover:bg-white/10 transition-colors lg:ml-2"
          >
            {menuOpen ? (
              <X className="w-5 h-5 text-slate-300" />
            ) : (
              <Menu className="w-5 h-5 text-slate-300" />
            )}
          </button>
        </div>
      </div>

      {/* ═══ Dropdown Mega Menu ═══ */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden border-t border-slate-700 bg-[#0B1120]"
          >
            <div className="px-6 py-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
              {HAMBURGER_LINKS.map((group, idx) => (
                <motion.div
                  key={group.section}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05, duration: 0.25 }}
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

              {/* Mobile: show primary links too */}
              <div className="lg:hidden col-span-full border-t border-slate-700 pt-4 flex flex-wrap gap-2">
                {NAV_LINKS.map((link) => (
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