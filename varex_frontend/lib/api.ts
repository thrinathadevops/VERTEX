import axios from "axios";
import type {
  User, Subscription, ContentItem,
  PortfolioProject as Project, TeamMember, Certification,
  FAQ, Workshop, Lead,
} from "./types";

function resolveApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, "");

  // Browser requests should stay same-origin behind Nginx.
  if (typeof window !== "undefined") return window.location.origin;

  // Server-side fallback (Docker network).
  return "http://backend:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  withCredentials: true, // Crucial for sending httpOnly cookies
});

import { refreshAccessToken, login as authLogin, register as authRegister } from "./auth";

// ── Response interceptor: extract data or throw proper error ───────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const success = await refreshAccessToken();
      if (success) {
        return api(originalRequest);
      }
    }
    return Promise.reject(error.response?.data || error);
  }
);

// Authentication is handled in @/lib/auth.ts

// ════════════════════════════════════════════════════════════════
// USER
// ════════════════════════════════════════════════════════════════
export async function getMe(): Promise<User> {
  const res = await api.get<User>("/users/me");
  return res.data;
}

export async function login(payload: { email: string; password: string }) {
  return authLogin(payload.email, payload.password);
}

export async function register(payload: { name: string; email: string; password: string }) {
  return authRegister(payload.name, payload.email, payload.password);
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
  if (featured) params.append("featured_only", "true");
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
const founderProfile: TeamMember = {
  id: "founder-1",
  name: "Sai Charitha Chinthakunta",
  slug: "sai-charitha-chinthakunta",
  role: "Founder & CEO",
  title: "Founder & CEO, SAP SD Architect",
  bio: "With a deep specialization in SAP Sales & Distribution (SD) and large-scale enterprise deployments, Sai Charitha founded VAREX to bridge the gap between rigorous enterprise software practices and agile cloud infrastructure.",
  specializations: ["SAP SD", "Cloud Architecture", "Enterprise Deployments", "Technical Leadership"],
  tools: ["SAP ERP", "S/4HANA", "AWS", "Jira", "Confluence"],
  certifications: ["SAP Certified Application Associate - Sales and Distribution", "AWS Certified Cloud Practitioner"],
  linkedin_url: "https://www.linkedin.com/company/varextech",
  avatar_url: "/founder.jpg",
  display_order: 0,
  is_published: true,
  created_at: new Date().toISOString()
};

const devSecOpsProfile: TeamMember = {
  id: "team-thrinatha-1",
  name: "Thrinatha Reddy",
  slug: "thrinatha-reddy",
  role: "DevSecOps Engineer",
  title: "DevSecOps Engineer",
  bio: "A dedicated DevSecOps professional specializing in automating secure deployment pipelines, cloud infrastructure resilience, and continuous threat modeling. Thrinatha ensures security is ingrained seamlessly into high-velocity engineering workflows.",
  specializations: ["Cybersecurity", "CI/CD Pipelines", "Cloud Infrastructure", "Security Hardening"],
  tools: ["Docker", "Kubernetes", "AWS", "GitHub Actions", "Terraform", "Jenkins"],
  certifications: ["AWS Certified Security - Specialty", "Certified Kubernetes Security Specialist (CKS)"],
  linkedin_url: "https://www.linkedin.com/in/thrinatha",
  avatar_url: "/thrinatha.png",
  display_order: 1,
  is_published: true,
  created_at: new Date().toISOString()
};

export async function listTeam(): Promise<TeamMember[]> {
  try {
    const res = await api.get<TeamMember[]>("/team");
    return [founderProfile, devSecOpsProfile, ...res.data];
  } catch (error) {
    console.warn("Backend team fetch failed, returning mocked profiles only.", error);
    return [founderProfile, devSecOpsProfile];
  }
}

export async function getTeamMember(slug: string): Promise<TeamMember> {
  if (slug === founderProfile.slug) return founderProfile;
  if (slug === devSecOpsProfile.slug) return devSecOpsProfile;
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

export async function listAchievements(): Promise<any[]> {
  const res = await api.get<any[]>("/achievements");
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
  // Email sending is now handled concurrently inside the components (e.g., contact/page.tsx)
  return res.data;
}

// ════════════════════════════════════════════════════════════════
// ANALYTICS & INTERVIEW (Newly Added)
// ════════════════════════════════════════════════════════════════
export async function getAnalytics() {
  const res = await api.get("/analytics/");
  return res.data;
}

export async function createJobDescription(payload: {
  title: string; company?: string; description: string; skills?: string[];
}) {
  const res = await api.post("/interview/jd", payload);
  return res.data;
}

export async function uploadResume(jobId: string, file: File, candidateName: string, candidateEmail: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("job_id", jobId);
  form.append("name", candidateName);
  form.append("email", candidateEmail);
  const res = await api.post("/interview/candidate", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return res.data;
}

export async function startInterviewSession(jobId: string, candidateId: string) {
  const res = await api.post("/interview/session", { job_id: jobId, candidate_id: candidateId });
  return res.data;
}

export async function submitInterviewAnswer(sessionId: string, answer: string) {
  const res = await api.post(`/interview/session/${sessionId}/answer`, { answer });
  return res.data;
}

export async function getInterviewReport(sessionId: string) {
  const res = await api.get(`/interview/session/${sessionId}/report`);
  return res.data;
}

export async function runCalculator(calculator: string, payload: Record<string, unknown>) {
  const res = await api.post(`/calculators/${calculator}/calculate`, payload);
  return res.data;
}

export async function getCalculatorExample(calculator: string, profile: string) {
  const res = await api.post(`/calculators/${calculator}/example/${profile}`);
  return res.data;
}

export default api;

