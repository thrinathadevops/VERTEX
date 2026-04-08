// PATH: varex_frontend/lib/auth.ts
// FIX: No longer storing tokens in JS-accessible cookies
// Tokens are now httpOnly cookies set by the backend
// user data stored only in React state / sessionStorage (not editable role cookie)

"use client";

import { getMe } from "@/lib/api";
import type { User } from "@/lib/types";

function resolveApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (typeof window !== "undefined") {
    return "";
  }

  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "http://backend:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

// Login — POST to backend, which sets httpOnly cookies
export async function login(email: string, password: string): Promise<User> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/auth/login`,
    {
      method: "POST",
      credentials: "include",          // Send/receive cookies cross-origin
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "Login failed");
  }
  // Backend returns minimal user info — NOT the token
  return res.json();
}

// Logout — calls backend to blacklist token + clear cookies
export async function logout(): Promise<void> {
  try {
    await fetch(
      `${API_BASE_URL}/api/v1/auth/logout`,
      {
        method: "POST",
        credentials: "include",
      }
    );
  } catch { }
  // Clear any local state
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("varex_user");
  }
}

// clearTokens — synchronous helper that clears local state and calls logout async
export function clearTokens(): void {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("varex_user");
  }
  // The original fetch might fail but we just clear state
  logout().catch(() => { });
}

// setTokens — stores user in session storage
export function setTokens(user: User): void {
  if (typeof window !== "undefined" && user) {
    sessionStorage.setItem("varex_user", JSON.stringify(user));
  }
}

// getUserFromCookies — synchronous helper returning user from session storage
export function getUserFromCookies(): User | null {
  if (typeof window !== "undefined") {
    const cached = sessionStorage.getItem("varex_user");
    if (cached) return JSON.parse(cached) as User;
  }
  return null;
}

// Register
export async function register(name: string, email: string, password: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/auth/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "Registration failed");
  }
}

// Get current user — always fetched from backend (not from cookie)
// Cache result in sessionStorage to avoid repeat calls on same tab
export async function getCurrentUser(): Promise<User | null> {
  try {
    if (typeof window !== "undefined") {
      const cached = sessionStorage.getItem("varex_user");
      if (cached) return JSON.parse(cached) as User;
    }
    const user = await getMe();
    if (typeof window !== "undefined") {
      sessionStorage.setItem("varex_user", JSON.stringify(user));
    }
    return user;
  } catch {
    return null;
  }
}

// Refresh access token using refresh cookie
export async function refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/auth/refresh`,
      {
        method: "POST",
        credentials: "include",
      }
    );
    return res.ok;
  } catch {
    return false;
  }
}

