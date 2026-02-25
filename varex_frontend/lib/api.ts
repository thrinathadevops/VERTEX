// ─────────────────────────────────────────────────────────────────
// lib/api.ts  —  VAREX Platform  (complete)
// ─────────────────────────────────────────────────────────────────
import axios from "axios";
import Cookies from "js-cookie";
import type {
  Tokens, User, Subscription, ContentItem,
  Project, TeamMember, Certification, Achievement,
  FAQ, Workshop, Lead,
} from "./types";
import { setTokens as storeTokens } from "./auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
});

// ── Request interceptor: attach Bearer token ──────────────────────
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: auto-refresh on 401 ────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = Cookies.get("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post<Tokens>(
            `${API_BASE_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken }
          );
          storeTokens(res.data);
          originalRequest.headers = originalRequest.headers ?? {};
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(originalRequest);
        } catch {
          // refresh failed — fall through
        }
      }
    }
    return Promise.reject(error);
  }
);

// ════════════════════════════════════════════════════════════════
// AUTH
// ════════════════════════════════════════════════════════════════
export interface LoginPayload    { email: string; password: string }
export interface RegisterPayload { name: string; email: string; password: string }

export async function login(payload: LoginPayload): Promise<Tokens> {
  const res = await api.post<Tokens>("/auth/login", payload);
  return res.data;
}

export async function register(payload: RegisterPayload) {
  const res = await api.post("/auth/register", payload);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// USER
// ════════════════════════════════════════════════════════════════
export async function getMe(): Promise<User> {
  const res = await api.get<User>("/users/me");
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// SUBSCRIPTION
// ════════════════════════════════════════════════════════════════
export async function getMySubscription(): Promise<Subscription> {
  const res = await api.get<Subscription>("/subscriptions/me");
  return res.data;
}

export async function createSubscription(plan_type: string): Promise<Subscription> {
  const res = await api.post<Subscription>(`/subscriptions?plan_type=${plan_type}`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// CONTENT / BLOG
// ════════════════════════════════════════════════════════════════
export async function listFreeContent(): Promise<ContentItem[]> {
  const res = await api.get<ContentItem[]>("/content/free");
  return res.data;
}

export async function listPremiumContent(): Promise<ContentItem[]> {
  const res = await api.get<ContentItem[]>("/content/premium");
  return res.data;
}

export async function getContentBySlug(slug: string): Promise<ContentItem> {
  const res = await api.get<ContentItem>(`/content/${slug}`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// PORTFOLIO / PROJECTS
// ════════════════════════════════════════════════════════════════
export async function listProjects(
  category?: string,
  featured?: boolean
): Promise<Project[]> {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  if (featured)  params.append("featured_only", "true");
  const res = await api.get<Project[]>(`/portfolio?${params}`);
  return res.data;
}

export async function getProject(slug: string): Promise<Project> {
  const res = await api.get<Project>(`/portfolio/${slug}`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// TEAM
// ════════════════════════════════════════════════════════════════
export async function listTeam(): Promise<TeamMember[]> {
  const res = await api.get<TeamMember[]>("/team");
  return res.data;
}

export async function getTeamMember(slug: string): Promise<TeamMember> {
  const res = await api.get<TeamMember>(`/team/${slug}`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// CERTIFICATIONS & ACHIEVEMENTS
// ════════════════════════════════════════════════════════════════
export async function listCertifications(domain?: string): Promise<Certification[]> {
  const params = domain ? `?domain=${domain}` : "";
  const res = await api.get<Certification[]>(`/certifications${params}`);
  return res.data;
}

export async function listAchievements(): Promise<Achievement[]> {
  const res = await api.get<Achievement[]>("/certifications/achievements");
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// FAQ
// ════════════════════════════════════════════════════════════════
export async function listFAQs(category?: string): Promise<FAQ[]> {
  const params = category ? `?category=${category}` : "";
  const res = await api.get<FAQ[]>(`/faq${params}`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// WORKSHOPS
// ════════════════════════════════════════════════════════════════
export async function listWorkshops(): Promise<Workshop[]> {
  const res = await api.get<Workshop[]>("/workshops");
  return res.data;
}

export async function getWorkshop(slug: string): Promise<Workshop> {
  const res = await api.get<Workshop>(`/workshops/${slug}`);
  return res.data;
}

export async function registerWorkshop(workshopId: string): Promise<unknown> {
  const res = await api.post(`/workshops/${workshopId}/register`);
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// LEADS / CONSULTATION
// ════════════════════════════════════════════════════════════════
export interface LeadPayload {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  service_interest: string;
  message?: string;
  preferred_slot?: string;
}

export async function submitLead(payload: LeadPayload): Promise<Lead> {
  const res = await api.post<Lead>("/leads", payload);
  return res.data;
}
