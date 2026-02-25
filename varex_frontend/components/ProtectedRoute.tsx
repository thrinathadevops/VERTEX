// PATH: varex_frontend/components/ProtectedRoute.tsx
// FULL FINAL FILE — single export, no duplicates
// FIX: Two conflicting default exports merged into one
// FIX: getCurrentUser (server-validated) used — NOT getUserFromCookies (client-editable)
// FIX: allowedRoles support retained
// FIX: ?next= redirect param preserved for post-login redirect
// FIX: usePathname imported and used

"use client";

import { useEffect, useState }         from "react";
import { useRouter, usePathname }       from "next/navigation";
import { getCurrentUser }               from "@/lib/auth";   // validates via GET /users/me
import type { User }                    from "@/lib/types";

interface Props {
  children:     React.ReactNode;
  allowedRoles?: string[];   // e.g. ["premium", "enterprise", "admin"]
}

export default function ProtectedRoute({ children, allowedRoles }: Props) {
  const router   = useRouter();
  const pathname = usePathname();

  const [user,    setUser]    = useState<User | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((u) => {
        // Not logged in — redirect to /login, preserve intended destination
        if (!u) {
          router.replace(`/login?next=${encodeURIComponent(pathname ?? "/")}`);
          return;
        }

        // Logged in but wrong role — redirect to dashboard
        if (allowedRoles && !allowedRoles.includes(u.role)) {
          router.replace("/dashboard");
          return;
        }

        setUser(u);
      })
      .catch(() => {
        // Network error / 401 — treat as unauthenticated
        router.replace(`/login?next=${encodeURIComponent(pathname ?? "/")}`);
      })
      .finally(() => setChecked(true));
  }, []);   // eslint-disable-line react-hooks/exhaustive-deps

  // Loading state
  if (!checked) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  // Render children only when user is confirmed
  return user ? <>{children}</> : null;
}