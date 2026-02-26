"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogIn, Rocket, Menu, X, Home, Briefcase, Award, Briefcase as Portfolio, Users, LayoutDashboard } from "lucide-react";
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
    <header className="sticky top-0 z-50 bg-[#0B1120] border-b border-slate-800 shadow-xl">
      <div className="mx-auto max-w-7xl flex items-center justify-between px-4 sm:px-6 lg:px-8 h-[70px]">

        {/* ═══ LOGO — LEFT ═══ */}
        <div className="flex-shrink-0">
          <Link href="/" className="flex items-center gap-2 transition-transform hover:scale-105 duration-200">
            <Image
              src="/varex-logo-enterprise.svg"
              alt="VAREX"
              width={140}
              height={40}
              priority
              className="h-10 w-auto object-contain"
            />
          </Link>
        </div>

        {/* ═══ NAV LINKS — CENTER (DESKTOP) ═══ */}
        <nav className="hidden md:flex items-center gap-2 lg:gap-4 flex-1 justify-center px-4">
          {NAV_LINKS.map((link) => {
            const IconComponent = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2 px-3 lg:px-4 py-2 rounded-md text-xs lg:text-sm font-medium transition-colors ${isActive
                    ? "bg-slate-800 text-cyan-400"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
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
            <div className="flex items-center gap-3">
              <span className="hidden lg:inline text-slate-400 text-sm">
                {user.email}
              </span>
              <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs capitalize text-cyan-400 border border-cyan-500/20">
                {user.role.replace("_", " ")}
              </span>
              <button
                onClick={handleLogout}
                className="hidden sm:flex items-center gap-2 rounded-md border border-slate-700 hover:border-red-500 hover:text-red-400 px-4 py-2 text-sm font-medium text-slate-300 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden lg:inline">Sign out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 md:gap-3">
              <Link
                href="/login"
                className="hidden sm:flex items-center gap-2 rounded-md border border-slate-700 hover:border-cyan-400 hover:text-cyan-400 px-4 py-2 text-sm font-medium text-slate-300 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden lg:inline">Sign in</span>
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-md bg-cyan-600 hover:bg-cyan-500 px-4 py-2 text-sm font-medium text-white transition-colors"
              >
                <Rocket className="w-4 h-4" />
                <span className="hidden lg:inline">Get Started</span>
              </Link>
            </div>
          )}

          {/* ═══ MOBILE MENU TOGGLE ═══ */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* ═══ MOBILE MENU DROPDOWN ═══ */}
      {menuOpen && (
        <nav className="md:hidden border-t border-slate-800 bg-[#0B1120] px-4 py-4 space-y-2">
          {NAV_LINKS.map((link) => {
            const IconComponent = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors ${isActive
                    ? "bg-slate-800 text-cyan-400"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
              >
                <IconComponent className="w-5 h-5" />
                {link.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}