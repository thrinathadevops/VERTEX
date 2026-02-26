"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserFromCookies, clearTokens } from "@/lib/auth";
import type { User } from "@/lib/types";

const NAV_LINKS = [
  { href: "/", label: "HOME" },
  { href: "/services", label: "SERVICES" },
  { href: "/hire", label: "HIRE" },
  { href: "/portfolio", label: "PORTFOLIO" },
  { href: "/team", label: "TEAM" },
  { href: "/dashboard", label: "DASHBOARD" },
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
    <header className="sticky top-0 z-50 bg-[#0f172a] border-b-[3px] border-[#06b6d4]">
      <div className="mx-auto max-w-7xl flex items-center justify-between px-6 h-16">

        {/* LOGO — left */}
        <Link href="/" className="flex-shrink-0">
          <Image
            src="/varex-logo.png"
            alt="VAREX"
            width={140}
            height={40}
            priority
            className="h-10 w-auto object-contain"
          />
        </Link>

        {/* NAV LINKS — center (desktop) */}
        <nav className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href}
              className={`text-sm font-semibold tracking-wide transition-colors ${pathname === link.href
                  ? "text-[#06b6d4]"
                  : "text-gray-300 hover:text-white"
                }`}>
              {link.label}
            </Link>
          ))}
        </nav>

        {/* AUTH — right */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden lg:inline text-gray-400 text-xs">{user.email}</span>
              <span className="text-xs text-[#06b6d4] font-semibold capitalize">
                {user.role.replace("_", " ")}
              </span>
              <button onClick={handleLogout}
                className="text-sm text-gray-300 hover:text-red-400 transition-colors">
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login"
                className="hidden sm:block text-sm font-medium text-gray-300 hover:text-white transition-colors">
                Sign in
              </Link>
              <Link href="/register"
                className="text-sm font-bold text-white bg-[#06b6d4] hover:bg-[#0891b2] px-4 py-2 rounded-md transition-colors">
                Get Started
              </Link>
            </>
          )}

          {/* HAMBURGER — mobile */}
          <button onClick={() => setMenuOpen(v => !v)} className="md:hidden p-1"
            aria-label="Menu">
            <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>
      </div>

      {/* MOBILE MENU */}
      {menuOpen && (
        <nav className="md:hidden border-t border-gray-700 bg-[#0f172a] px-6 py-4 space-y-2">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href} onClick={() => setMenuOpen(false)}
              className={`block py-2 text-sm font-semibold ${pathname === link.href ? "text-[#06b6d4]" : "text-gray-300"
                }`}>
              {link.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}