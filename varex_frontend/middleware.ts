import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_ROUTES = [
  "/dashboard",
  "/learnings",
  "/workshops",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  if (AUTH_ROUTES.some((r) => pathname.startsWith(r)) && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|images|fonts).*)",
  ],
};
