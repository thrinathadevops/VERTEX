/*
 * middleware.ts — VAREX Route Protection
 * Runs on every request. Redirects unauthenticated users away from
 * protected routes, and non-premium users away from premium routes.
 *
 * Place this file at: varex-frontend/middleware.ts  (project root)
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that require at minimum a logged-in free user
const AUTH_ROUTES = [
  "/dashboard",
  "/learnings",
  "/workshops",
];

// Routes that require premium or above
const PREMIUM_ROUTES = [
  "/learnings/premium",
  "/blog/premium",
];

// Routes that require enterprise
const ENTERPRISE_ROUTES = [
  "/dashboard/enterprise",
  "/reports",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;
  const role  = request.cookies.get("user_role")?.value ?? "guest";

  const ROLE_RANK: Record<string, number> = {
    guest: 0, free_user: 1, premium: 2, enterprise: 3, admin: 99,
  };
  const userRank = ROLE_RANK[role] ?? 0;

  // 1. Must be logged in
  if (AUTH_ROUTES.some((r) => pathname.startsWith(r)) && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  // 2. Must be premium
  if (PREMIUM_ROUTES.some((r) => pathname.startsWith(r)) && userRank < 2) {
    const url = request.nextUrl.clone();
    url.pathname = "/pricing";
    url.searchParams.set("required", "premium");
    return NextResponse.redirect(url);
  }

  // 3. Must be enterprise
  if (ENTERPRISE_ROUTES.some((r) => pathname.startsWith(r)) && userRank < 3) {
    const url = request.nextUrl.clone();
    url.pathname = "/pricing";
    url.searchParams.set("required", "enterprise");
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|images|fonts).*)",
  ],
};
