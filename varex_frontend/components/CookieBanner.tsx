// PATH: components/CookieBanner.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Cookie } from "lucide-react";

type Consent = "accepted" | "rejected" | null;

export default function CookieBanner() {
  const [consent, setConsent] = useState<Consent>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("varex_cookie_consent") as Consent;
    if (!stored) {
      // Slight delay so it doesn't flash on first render
      const t = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(t);
    }
    setConsent(stored);
  }, []);

  const accept = () => {
    localStorage.setItem("varex_cookie_consent", "accepted");
    setConsent("accepted");
    setVisible(false);
  };

  const reject = () => {
    localStorage.setItem("varex_cookie_consent", "rejected");
    setConsent("rejected");
    setVisible(false);
  };

  if (!visible || consent !== null) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-sm
        z-50 rounded-2xl border border-slate-700 bg-slate-900 p-4 shadow-2xl
        shadow-black/40 animate-in slide-in-from-bottom-4 duration-300"
    >
      <p className="text-xs font-semibold text-slate-100 mb-1 inline-flex items-center gap-1.5">
        <Cookie className="h-3.5 w-3.5 text-amber-300" />
        Cookies
      </p>
      <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
        We use strictly necessary cookies for authentication, and optional analytics
        cookies to improve the platform. See our{" "}
        <Link href="/privacy" className="text-sky-400 hover:text-sky-300 underline">
          Privacy Policy
        </Link>
        .
      </p>
      <div className="flex gap-2">
        <button onClick={accept}
          className="flex-1 rounded-md bg-sky-500 px-3 py-1.5 text-xs font-semibold
            text-white hover:bg-sky-400 transition">
          Accept all
        </button>
        <button onClick={reject}
          className="flex-1 rounded-md border border-slate-700 px-3 py-1.5 text-xs
            text-slate-300 hover:border-slate-500 transition">
          Necessary only
        </button>
      </div>
    </div>
  );
}
