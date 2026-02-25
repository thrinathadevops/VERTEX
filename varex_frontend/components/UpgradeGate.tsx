"use client";
import Link from "next/link";

interface Props {
  requiredPlan?: "premium" | "enterprise";
  children: React.ReactNode;
  userRole?: string;
}

const PLAN_RANK: Record<string, number> = {
  guest: 0, free_user: 1, premium: 2, enterprise: 3, admin: 99
};

export default function UpgradeGate({ requiredPlan = "premium", children, userRole = "guest" }: Props) {
  const required = PLAN_RANK[requiredPlan] ?? 2;
  const current  = PLAN_RANK[userRole] ?? 0;

  if (current >= required) return <>{children}</>;

  return (
    <div className="relative rounded-2xl border border-slate-700 bg-slate-900/70 overflow-hidden">
      {/* Blurred preview */}
      <div className="pointer-events-none select-none blur-sm opacity-30 p-6">
        {children}
      </div>
      {/* Overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm p-6 text-center">
        <span className="text-2xl mb-2">🔒</span>
        <h3 className="text-sm font-semibold mb-1">
          {requiredPlan === "enterprise" ? "Enterprise" : "Premium"} content
        </h3>
        <p className="text-xs text-slate-300 mb-4 max-w-xs">
          Upgrade your plan to unlock this content and get full access to all VAREX resources.
        </p>
        <Link href="/pricing"
          className="rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
          View pricing plans
        </Link>
      </div>
    </div>
  );
}
