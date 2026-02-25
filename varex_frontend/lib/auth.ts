
"use client";

import Cookies from "js-cookie";
import jwtDecode from "jwt-decode";
import type { Tokens, User } from "./types";

export function setTokens(tokens: Tokens) {
  Cookies.set("access_token", tokens.access_token, { sameSite: "lax" });
  Cookies.set("refresh_token", tokens.refresh_token, { sameSite: "lax" });

  try {
    const decoded: any = jwtDecode(tokens.access_token);
    Cookies.set("user_id", decoded.sub, { sameSite: "lax" });
  } catch {
    // ignore
  }
}

export function clearTokens() {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
  Cookies.remove("user_id");
}

export function getUserFromCookies(): User | null {
  const raw = Cookies.get("user_cache");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function cacheUser(user: User) {
  Cookies.set("user_cache", JSON.stringify(user), { sameSite: "lax" });
}
