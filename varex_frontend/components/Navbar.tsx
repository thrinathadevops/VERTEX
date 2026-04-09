"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { LogIn, LogOut, Rocket, Menu, X, Home, Briefcase, Award, Briefcase as Portfolio, Users, LayoutDashboard, Bot, Calculator, FileText, Lock } from "lucide-react";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const NAV_LINKS = [
  { href: "/", label: "HOME", icon: Home },
  { href: "/services", label: "SERVICES", icon: Briefcase },
  { href: "/hire", label: "HIRE", icon: Award },
  { href: "/calculator", label: "CALCULATOR", icon: Calculator },
  { href: "/portfolio", label: "PORTFOLIO", icon: Portfolio },
  { href: "/blog", label: "BLOG", icon: FileText },
  { href: "/team", label: "TEAM", icon: Users },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    setUser(getUserFromCookies());
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    router.push("/");
  };

  const navLinks = user
    ? [...NAV_LINKS, { href: "/dashboard", label: "DASHBOARD", icon: LayoutDashboard }]
    : NAV_LINKS;

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${isScrolled
          ? "border-b border-white/20 bg-white/10 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.15)]"
          : "border-b border-white/10 bg-transparent"
        }`}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 top-0 h-24 w-72 rounded-full bg-emerald-400/10 blur-[70px]" />
        <div className="absolute left-1/3 top-[-18px] h-20 w-56 rounded-full bg-cyan-400/10 blur-[60px]" />
        <div className="absolute -right-16 top-0 h-24 w-64 rounded-full bg-indigo-500/10 blur-[72px]" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-emerald-400/35 to-transparent" />
      </div>
      <div
        className={`mx-auto max-w-7xl flex items-center justify-between px-3 sm:px-5 lg:px-7 transition-[height] duration-300 ${isScrolled ? "h-[62px]" : "h-[68px]"
          }`}
      >

        {/* ═══ LOGO — LEFT ═══ */}
        <div className="flex-shrink-0">
          <Link href="/" className="flex items-center gap-2 transition-transform hover:scale-[1.02] duration-200">
            <Image
              src="/varex-logo-enterprise.svg"
              alt="VAREX"
              width={188}
              height={52}
              priority
              className={`w-auto object-contain transition-[height] duration-300 ${isScrolled ? "h-10" : "h-11"
                }`}
            />
          </Link>
        </div>

        {/* ═══ NAV LINKS — CENTER (DESKTOP) ═══ */}
        <nav className="hidden md:flex items-center gap-1.5 lg:gap-2.5 flex-1 justify-center px-3">
          {navLinks.map((link) => {
            const IconComponent = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex min-h-11 items-center gap-1.5 px-2.5 lg:px-3.5 py-1.5 rounded-md text-[11px] lg:text-xs font-semibold tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 ${isActive
                    ? "bg-[linear-gradient(135deg,rgba(14,165,233,0.16),rgba(16,185,129,0.12))] text-sky-200 ring-1 ring-sky-400/40 shadow-[0_0_0_1px_rgba(16,185,129,0.12),0_12px_28px_rgba(8,145,178,0.14)]"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/70 hover:ring-1 hover:ring-emerald-400/20"
                  }`}
              >
                <IconComponent className="w-4 h-4 hidden lg:inline" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* ═══ AUTH BUTTONS — RIGHT ═══ */}
        <div className="flex items-center gap-3 md:gap-4 ml-auto">
          {user ? (
            <div className="flex items-center gap-2.5">
              <span className="hidden xl:inline text-slate-400 text-xs">
                {user.email}
              </span>
              <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-[11px] capitalize text-cyan-300 border border-cyan-500/20">
                {user.role.replace("_", " ")}
              </span>
              <button
                onClick={handleLogout}
                className="hidden sm:flex min-h-11 items-center gap-1.5 rounded-md border border-slate-700 hover:border-red-500 hover:text-red-400 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden xl:inline">Sign out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 md:gap-2">
              <Link
                href="/login"
                className="hidden sm:flex min-h-11 items-center gap-1.5 rounded-md border border-slate-700 hover:border-cyan-400 hover:text-cyan-400 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden xl:inline">Sign in</span>
              </Link>
              <Link
                href="/register"
                className="inline-flex min-h-11 items-center gap-1.5 rounded-md bg-[linear-gradient(135deg,#0891b2,#0ea5e9)] hover:brightness-110 px-3 py-1.5 text-xs font-semibold text-white transition-all shadow-[0_14px_30px_rgba(14,165,233,0.22)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
              >
                <Rocket className="w-4 h-4" />
                <span className="hidden xl:inline">Get Started</span>
              </Link>
            </div>
          )}

          {/* ═══ MOBILE MENU TOGGLE ═══ */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden min-h-11 min-w-11 p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* ═══ MOBILE MENU DROPDOWN ═══ */}
      <AnimatePresence initial={false}>
      {menuOpen && (
        <motion.nav
          initial={{ opacity: 0, y: -10, height: 0 }}
          animate={{ opacity: 1, y: 0, height: "auto" }}
          exit={{ opacity: 0, y: -8, height: 0 }}
          transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
          className="md:hidden overflow-hidden border-t border-slate-800 bg-[#0B1120]"
        >
          <div className="px-4 py-4 space-y-2">
          {navLinks.map((link) => {
            const IconComponent = link.icon;
            const isActive = pathname === link.href;
            return (
              <motion.div
                key={link.href}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.18 }}
              >
                <Link
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className={`flex min-h-11 items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 ${isActive
                      ? "bg-slate-800 text-cyan-400"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                    }`}
                >
                  <IconComponent className="w-5 h-5" />
                  {link.label}
                </Link>
              </motion.div>
            );
          })}
          </div>
        </motion.nav>
      )}
      </AnimatePresence>
    </header>
  );
}
