"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogIn, Rocket, Menu, X, Home, Briefcase, Award, Users, LayoutDashboard } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const NAV_LINKS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/services", label: "Services", icon: Briefcase },
  { href: "/hire", label: "Hire", icon: Award },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/team", label: "Team", icon: Users },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
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

// Animation variants
const headerVariants = {
  hidden: { opacity: 0, y: -10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const }
  }
};

const navLinkVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.08, duration: 0.4 }
  }),
  hover: {
    scale: 1.05,
    transition: { duration: 0.25 }
  }
};

const buttonVariants = {
  hover: { scale: 1.08, transition: { duration: 0.25 } },
  tap: { scale: 0.95 }
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
    <motion.div
      initial="hidden"
      animate="visible"
      variants={headerVariants}
    >
      <header
        className="sticky top-0 z-50 bg-gradient-to-r from-[#0B1120] via-[#1a2449] to-[#0B1120] border-b-[3px] border-cyan-400/80 shadow-2xl shadow-cyan-500/25"
      >
        {/* 
        Main header bar with improved styling
        Height: 70px (≈18.5mm on standard screen) 
        Layout: Logo (left) | Nav links (center) | Auth buttons (right)
      */}
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 h-[70px]">

          {/* ═══ LEFT: Company Logo with enhanced styling ═══ */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            <Link
              href="/"
              className="flex items-center gap-2 flex-shrink-0 hover:scale-105 transition-transform duration-300 group"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg blur opacity-50 group-hover:opacity-100 transition-opacity"></div>
                <Image
                  src="/varex-logo-enterprise.svg"
                  alt="VAREX"
                  width={140}
                  height={40}
                  priority
                  className="relative rounded-lg"
                />
              </div>
            </Link>
          </motion.div>

          {/* ═══ CENTER: Navigation Links (Desktop) ═══ */}
          <nav className="hidden lg:flex items-center gap-2 ml-8">
            {NAV_LINKS.map((link, i) => {
              const isActive = pathname === link.href;
              const IconComponent = link.icon;
              return (
                <motion.div
                  key={link.href}
                  custom={i}
                  initial="hidden"
                  animate="visible"
                  whileHover="hover"
                  variants={navLinkVariants}
                >
                  <Link
                    href={link.href}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${isActive
                      ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/50"
                      : "text-slate-300 hover:text-cyan-300 hover:bg-slate-800/50 border border-transparent hover:border-cyan-500/30"
                      }`}
                  >
                    <IconComponent className="w-4 h-4" />
                    {link.label}
                  </Link>
                </motion.div>
              );
            })}
          </nav>

          {/* ═══ RIGHT: Auth Buttons + Hamburger ═══ */}
          <div className="flex items-center gap-4 ml-auto">
            {user ? (
              <motion.div
                className="flex items-center gap-3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                <span className="hidden md:inline text-slate-400 text-xs">
                  {user.email}
                </span>
                <motion.span
                  className="rounded-full bg-cyan-500/20 px-3 py-1 text-xs capitalize text-cyan-300 font-semibold border border-cyan-500/50"
                  whileHover={{ scale: 1.05 }}
                >
                  {user.role.replace("_", " ")}
                </motion.span>
                <motion.button
                  onClick={handleLogout}
                  whileHover="hover"
                  whileTap="tap"
                  variants={buttonVariants}
                  className="flex items-center gap-1.5 rounded-lg border-2 border-slate-600 hover:border-red-500/80 px-4 py-2 text-sm font-semibold text-slate-200 hover:text-red-400 transition-all duration-300 hover:bg-red-500/10"
                >
                  <LogIn className="w-4 h-4" />
                  Sign out
                </motion.button>
              </motion.div>
            ) : (
              <motion.div
                className="flex items-center gap-3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                {/* Sign In button with icon */}
                <motion.div
                  whileHover="hover"
                  whileTap="tap"
                  variants={buttonVariants}
                >
                  <Link
                    href="/login"
                    className="hidden sm:inline-flex items-center gap-2 rounded-lg border-2 border-cyan-400/60 hover:border-cyan-300 px-4 py-2 text-sm font-semibold text-slate-200 hover:text-cyan-300 transition-all duration-300 hover:bg-cyan-500/10"
                  >
                    <LogIn className="w-4 h-4" />
                    Sign in
                  </Link>
                </motion.div>

                {/* Get Started button with icon */}
                <motion.div
                  whileHover="hover"
                  whileTap="tap"
                  variants={buttonVariants}
                >
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 px-5 py-2 text-sm font-bold text-white transition-all duration-300 shadow-lg shadow-cyan-500/50 hover:shadow-cyan-400/60"
                  >
                    <Rocket className="w-4 h-4" />
                    Get Started
                  </Link>
                </motion.div>
              </motion.div>
            )}

            {/* Hamburger / More Menu button */}
            <motion.button
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Open menu"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="ml-2 p-2 rounded-lg hover:bg-cyan-500/20 transition-all duration-300 lg:ml-3"
            >
              {menuOpen ? (
                <X className="w-5 h-5 text-cyan-400" />
              ) : (
                <Menu className="w-5 h-5 text-cyan-400" />
              )}
            </motion.button>
          </div>
        </div>

        {/* ═══ Dropdown Mega Menu with smooth animations ═══ */}
        <AnimatePresence>
          {menuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0, y: -10 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={{ opacity: 0, height: 0, y: -10 }}
              transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
              className="overflow-hidden border-t-2 border-cyan-400/40 bg-gradient-to-b from-[#0B1120]/95 to-[#1a2449]/95 backdrop-blur-sm"
            >
              <div className="px-6 py-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
                {HAMBURGER_LINKS.map((group, idx) => (
                  <motion.div
                    key={group.section}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.08, duration: 0.3, ease: "easeOut" }}
                  >
                    <p className="mb-4 text-xs font-bold text-cyan-400 uppercase tracking-widest">
                      {group.section}
                    </p>
                    <ul className="space-y-2">
                      {group.links.map((link) => (
                        <li key={link.href}>
                          <motion.div
                            whileHover={{ x: 4 }}
                            transition={{ duration: 0.2 }}
                          >
                            <Link
                              href={link.href}
                              onClick={() => setMenuOpen(false)}
                              className={`block rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-300 ${pathname === link.href
                                ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30"
                                : "text-slate-400 hover:bg-slate-800/40 hover:text-cyan-300 border border-transparent hover:border-cyan-500/20"
                                }`}
                            >
                              {link.label}
                            </Link>
                          </motion.div>
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                ))}

                {/* Mobile: show primary links too */}
                <motion.div
                  className="lg:hidden col-span-full border-t border-slate-700/50 pt-6 flex flex-wrap gap-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.35, duration: 0.3 }}
                >
                  {NAV_LINKS.map((link, i) => {
                    const IconComponent = link.icon;
                    return (
                      <motion.div
                        key={link.href}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.35 + i * 0.05 }}
                        whileHover={{ scale: 1.05 }}
                      >
                        <Link
                          href={link.href}
                          onClick={() => setMenuOpen(false)}
                          className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-slate-800 to-slate-700/80 hover:from-cyan-500/20 hover:to-blue-500/20 px-4 py-2.5 text-sm font-medium text-slate-200 hover:text-cyan-300 transition-all duration-300 border border-slate-700 hover:border-cyan-500/30"
                        >
                          <IconComponent className="w-4 h-4" />
                          {link.label}
                        </Link>
                      </motion.div>
                    );
                  })}
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>
    </motion.div>
  );
}