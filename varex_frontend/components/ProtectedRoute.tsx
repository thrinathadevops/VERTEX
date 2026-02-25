
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getUserFromCookies } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = getUserFromCookies();
    if (!u) {
      router.replace(`/login?next=${encodeURIComponent(pathname ?? "/")}`);
    } else {
      setUser(u);
    }
    setLoading(false);
  }, [router, pathname]);

  if (loading) {
    return <p className="text-sm text-slate-300">Checking access...</p>;
  }

  if (!user) return null;

  return <>{children}</>;
}
