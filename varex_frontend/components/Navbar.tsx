"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogIn, Rocket, Menu, X, Home, Briefcase, Award, Briefcase as Portfolio, Users, LayoutDashboard } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const NAV_LINKS = [
  { href: "/", label: "HOME", icon: Home },
  { href: "/services", label: "SERVICES", icon: Briefcase },
  { href: "/hire", label: "HIRE", icon: Award },
  { href: "/portfolio", label: "PORTFOLIO", icon: Portfolio },
  { href: "/team", label: "TEAM", icon: Users },
  { href: "/dashboard", label: "DASHBOARD", icon: LayoutDashboard },
];

const headerVariants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
};

const navLinkVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.1 + i * 0.08, duration: 0.4 }
  })
};

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setUser(getUserFromCookies());
    setMenuOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    router.push("/");
  };

  if (!mounted) return null;

  return (
    <motion.header
      initial="hidden"
      animate="visible"
      variants={headerVariants}
      className="sticky top-0 z-50 bg-gradient-to-r from-[#0B1120] via-[#1a2449] to-[#0B1120] border-b-[3px] border-cyan-400/80 shadow-2xl shadow-cyan-500/25"
    >
      <div className="mx-auto max-w-7xl flex items-center justify-between px-4 sm:px-6 lg:px-8 h-[70px]">

        {/* ═══ LOGO — LEFT ═══ */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="flex-shrink-0"
        >
          <Link href="/" className="flex items-center gap-2 group hover:scale-105 transition-transform duration-300">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg blur opacity-50 group-hover:opacity-100 transition-opacity"></div>
              <Image
                src="/varex-logo-enterprise.svg"
                alt="VAREX"
                width={140}
                height={40}
                priority
                className="relative h-10 w-auto object-contain"
              />
            </div>
          </Link>
        </motion.div>

        {/* ═══ NAV LINKS — CENTER (DESKTOP) ═══ */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2 flex-1 justify-center px-4">
          {NAV_LINKS.map((link, i) => {
            const IconComponent = link.icon;
            const isActive = pathname === link.href;
            return (
              <motion.div
                key={link.href}
                custom={i}
                initial="hidden"
                animate="visible"
                variants={navLinkVariants}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href={link.href}
                  className={`flex items-center gap-1.5 px-3 lg:px-4 py-2 rounded-lg text-xs lg:text-sm font-semibold transition-all duration-300 ${isActive
                    ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/50"
                    : "text-slate-300 hover:text-cyan-300 hover:bg-slate-800/50 border border-transparent hover:border-cyan-500/30"
                  }`}
                >
                  <IconComponent className="w-4 h-4 hidden lg:inline" />
                  <span>{link.label}</span>
                </Link>
              </motion.div>
            );
          })}
        </nav>

        {/* ═══ AUTH BUTTONS — RIGHT ═══ */}
        <motion.div
          className="flex items-center gap-2 sm:gap-3 ml-auto"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          {user ? (
            <>
              <span className="hidden lg:inline text-slate-400 text-xs">
                {user.email}
              </span>
              <motion.span
                className="rounded-full bg-cyan-500/20 px-2 lg:px-3 py-1 text-xs capitalize text-cyan-300 font-semibold border border-cyan-500/50"
                whileHover={{ scale: 1.05 }}
              >
                {user.role.replace("_", " ")}
              </motion.span>
              <motion.button
                onClick={handleLogout}
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.95 }}
                className="hidden sm:flex items-center gap-1.5 rounded-lg border-2 border-slate-600 hover:border-red-500/80 px-3 lg:px-4 py-1.5 lg:py-2 text-xs lg:text-sm font-semibold text-slate-200 hover:text-red-400 transition-all duration-300 hover:bg-red-500/10"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden lg:inline">Sign out</span>
              </motion.button>
            </>
          ) : (
            <>
              {/* Sign In Button */}
              <motion.div
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="/login"
                  className="hidden sm:flex items-center gap-1.5 rounded-lg border-2 border-cyan-400/60 hover:border-cyan-300 px-3 lg:px-4 py-1.5 lg:py-2 text-xs lg:text-sm font-semibold text-slate-200 hover:text-cyan-300 transition-all duration-300 hover:bg-cyan-500/10"
                >
                  <LogIn className="w-4 h-4" />
                  <span className="hidden lg:inline">Sign in</span>
                </Link>
              </motion.div>

              {/* Get Started Button */}
              <motion.div
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="/register"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 px-3 lg:px-5 py-1.5 lg:py-2 text-xs lg:text-sm font-bold text-white transition-all duration-300 shadow-lg shadow-cyan-500/50 hover:shadow-cyan-400/60"
                >
                  <Rocket className="w-4 h-4" />
                  <span className="hidden lg:inline">Get Started</span>
                </Link>
              </motion.div>
            </>
          )}

          {/* ═══ HAMBURGER MENU — MOBILE ═══ */}
          <motion.button
            onClick={() => setMenuOpen((v) => !v)}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Menu"
            className="md:hidden p-2 rounded-lg hover:bg-cyan-500/20 transition-all duration-300"
          >
            {menuOpen ? (
              <X className="w-5 h-5 text-cyan-400" />
            ) : (
              <Menu className="w-5 h-5 text-cyan-400" />
            )}
          </motion.button>
        </motion.div>
      </div>

      {/* ═══ MOBILE MENU ═══ */}
      <AnimatePresence>
        {menuOpen && (
          <motion.nav
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="md:hidden overflow-hidden border-t-2 border-cyan-400/40 bg-gradient-to-b from-[#0B1120]/95 to-[#1a2449]/95"
          >
            <div className="px-4 sm:px-6 py-4 space-y-2">
              {NAV_LINKS.map((link, i) => {
                const IconComponent = link.icon;
                const isActive = pathname === link.href;
                return (
                  <motion.div
                    key={link.href}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.05, duration: 0.3 }}
                    whileHover={{ x: 4 }}
                  >
                    <Link
                      href={link.href}
                      onClick={() => setMenuOpen(false)}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${isActive
                        ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30"
                        : "text-slate-400 hover:text-cyan-300 hover:bg-slate-800/40 border border-transparent hover:border-cyan-500/20"
                      }`}
                    >
                      <IconComponent className="w-4 h-4" />
                      {link.label}
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </motion.header>
  );
}