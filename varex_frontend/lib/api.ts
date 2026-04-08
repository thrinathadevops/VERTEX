import axios from "axios";
import type {
  User, Subscription, ContentItem,
  PortfolioProject as Project, TeamMember, Certification,
  FAQ, Workshop, Lead,
} from "./types";

function resolveApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (typeof window !== "undefined") {
    // Always use same-origin in the browser and let Next.js/nginx proxy /api/v1.
    return "";
  }

  if (fromEnv) return fromEnv.replace(/\/$/, "");

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

const cicdBlogPost: ContentItem = {
  id: "blog-cicd-1",
  title: "5 CI/CD Pipeline Best Practices Every DevSecOps Engineer Should Know",
  slug: "cicd-best-practices",
  body: `
<p>A poorly built CI/CD pipeline doesn't just slow down deployments—it acts as an open backdoor to your production databases. When building enterprise-grade infrastructure at VAREX, we treat pipelines exactly like production code: immutable, secure, and blazing fast.</p>

<p>Here are the 5 non-negotiable CI/CD architecture principles your team must adopt to safely scale deployment velocity.</p>

<h2>1. Shift-Left Security (DevSecOps Integration)</h2>
<p>Waiting to run security scans in staging or production is a critical anti-pattern. Vulnerabilities must be caught immediately upon commit. You must "shift left" by embedding Static Application Security Testing (SAST) and Dependency Scanning directly into your initial build stages.</p>

<blockquote><p>⚠️ <strong>Critical Rule:</strong> If a developer pushes code containing a known high-severity vulnerability (like a critical CVE in an NPM package), the CI pipeline must outright fail the build and block the merge request.</p></blockquote>

<h2>2. Build Once, Deploy Everywhere (Immutability)</h2>
<p>Never recompile code or rebuild Docker images between environments. Your CI system should build your artifact exactly <strong>once</strong>, tag it with a unique SHA or version, and store it in a secure registry (like AWS ECR or GitHub Packages).</p>
<p>Your CD system then simply takes that exact, unchanging artifact and promotes it through Dev ➔ Staging ➔ Production. This guarantees you are deploying the exact same code you tested.</p>

<h2>3. Fail Fast</h2>
<p>Engineering velocity requires immediate feedback. Structure your pipeline sequentially to run the fastest checks first.</p>
<ul>
<li><strong>0-1 Min:</strong> Code Linting, Secret Scanning (Trivy), Unit Tests</li>
<li><strong>1-5 Mins:</strong> Integration Tests, SAST (SonarQube)</li>
<li><strong>10+ Mins:</strong> Heavy End-to-End browser tests (Playwright)</li>
</ul>
<p>If there is a syntax error or a leaked AWS key, the pipeline should reject the commit in 15 seconds, not 45 minutes.</p>

<h2>4. Never Hardcode Secrets in Pipelines</h2>
<p>Modern CI/CD environments are highly targeted by attackers. Hardcoding database passwords or AWS keys into your <code>.gitlab-ci.yml</code> or GitHub Actions workflows is a fatal error.</p>
<p>Instead, strictly utilize <strong>OIDC (OpenID Connect)</strong> to assume short-lived cloud roles, or fetch temporary credentials dynamically from an encrypted vault like AWS Secrets Manager or HashiCorp Vault during runtime.</p>

<pre><code class="language-yaml"># Example: Using OIDC strictly instead of static AWS Access Keys
steps:
  - name: Configure AWS Credentials using OIDC
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::1234567890:role/GitHubActionsRole
      aws-region: us-east-1
</code></pre>

<h2>5. Treat Infrastructure as Code (IaC)</h2>
<p>Your pipeline itself, as well as the environments it provisions, should be stored alongside the application source code. Whether using Terraform or AWS CDK, your CI/CD agent must execute the infrastructure changes autonomously.</p>
<p>No human should be clicking buttons in the AWS Console to deploy an app. It must be reproducible, version-controlled, and transparent.</p>

<hr />
<p><strong>Ready to transform your cloud engineering workflows?</strong> At VAREX, we architect customized, threat-resilient CI/CD pipelines for enterprise ecosystems. <a href="/contact">Connect with us</a> to schedule a technical architecture review.</p>
`,
  category: "devops",
  access_level: "free",
  is_published: true,
  author_id: "founder-1",
  created_at: new Date().toISOString()
};

export async function listFreeContent(): Promise<ContentItem[]> {
  try {
    // 1. Try to fetch from Native Local Markdown system (Option 2)
    let localPosts: ContentItem[] = [];
    try {
      const localRes = await fetch("/api/content/local");
      if (localRes.ok) {
        localPosts = await localRes.json();
      }
    } catch (e) {
      console.warn("Could not fetch local markdown posts");
    }

    // 2. Try to fetch from Backend Database system (Option 1)
    let backendPosts: ContentItem[] = [];
    try {
      const dbRes = await api.get<ContentItem[]>("/content/free");
      backendPosts = dbRes.data;
    } catch (error) {
      console.warn("Backend Postgres fetch failed. Disabling Option 1 DB posts.");
    }

    // 3. Try to fetch from GitHub Repository
    let githubPosts: ContentItem[] = [];
    try {
      const ghRes = await fetch("/api/content/github");
      if (ghRes.ok) {
        githubPosts = await ghRes.json();
      }
    } catch (e) {
      console.warn("Could not fetch GitHub markdown posts");
    }

    // Combine all three sources uniquely
    const combined = [...localPosts, ...backendPosts, ...githubPosts];
    
    // Sort combined by created date descending
    return combined.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    
  } catch (error) {
    console.error("Critical failure resolving Free Content.", error);
    return [];
  }
}

export async function listPremiumContent(): Promise<ContentItem[]> {
  const res = await api.get<ContentItem[]>("/content/premium");
  return res.data;
}

export async function getContentBySlug(slug: string): Promise<ContentItem> {
  // Try retrieving locally first
  try {
    const localRes = await fetch("/api/content/local");
    if (localRes.ok) {
      const localPosts: ContentItem[] = await localRes.json();
      const match = localPosts.find(p => p.slug === slug || p.id === slug);
      if (match) return match;
    }
  } catch (e) {
    // ignore
  }

  // Try GitHub content
  try {
    const ghRes = await fetch("/api/content/github");
    if (ghRes.ok) {
      const ghPosts: ContentItem[] = await ghRes.json();
      const match = ghPosts.find(p => p.slug === slug || p.id === slug);
      if (match) return match;
    }
  } catch (e) {
    // ignore
  }

  // Fallback to database
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

