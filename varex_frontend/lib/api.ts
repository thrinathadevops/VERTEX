// PATH: varex_frontend/lib/api.ts  — ADD these functions to your existing api.ts
// FIX 4.6: subscription plan keys match backend PlanType enum exactly
// FIX 4.7: interview endpoints added
// FIX 4.8: analytics endpoint added
// FIX 4.9: throw in production if NEXT_PUBLIC_API_BASE_URL not set

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "production"
    ? (() => { throw new Error("NEXT_PUBLIC_API_BASE_URL is not set in production"); })()
    : "http://localhost:8000");

// ── Analytics (admin) ────────────────────────────────────────────
export async function getAnalytics() {
  const res = await apiRequest("GET", "/api/v1/analytics/");
  return res.data;
}

// ── Subscriptions ────────────────────────────────────────────────
// plan_type values MUST match backend PlanType enum: "monthly" | "quarterly" | "enterprise"
export async function getMySubscription() {
  const res = await apiRequest("GET", "/api/v1/subscriptions/me");
  return res.data;
}

// ── Interview ────────────────────────────────────────────────────
export async function createJobDescription(payload: {
  title: string; company?: string; description: string; skills?: string[];
}) {
  const res = await apiRequest("POST", "/api/v1/interview/jd", payload);
  return res.data;
}

export async function uploadResume(jobId: string, file: File, candidateName: string, candidateEmail: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("job_id", jobId);
  form.append("name", candidateName);
  form.append("email", candidateEmail);
  const res = await fetch(`${BASE}/api/v1/interview/candidate`, {
    method: "POST",
    body:   form,
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  return res.json();
}

export async function startInterviewSession(jobId: string, candidateId: string) {
  const res = await apiRequest("POST", "/api/v1/interview/session", { job_id: jobId, candidate_id: candidateId });
  return res.data;
}

export async function submitInterviewAnswer(sessionId: string, answer: string) {
  const res = await apiRequest("POST", `/api/v1/interview/session/${sessionId}/answer`, { answer });
  return res.data;
}

export async function getInterviewReport(sessionId: string) {
  const res = await apiRequest("GET", `/api/v1/interview/session/${sessionId}/report`);
  return res.data;
}

function getToken(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/access_token=([^;]+)/);
  return match ? match[1] : "";
}
