"use client";

import { CSSProperties, FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Shield, ShieldAlert, ShieldCheck, StopCircle } from "lucide-react";

type UserProfile = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  company_name: string | null;
};

type LiveSession = {
  session_id: string;
  candidate_name: string;
  candidate_email: string;
  target_role: string;
  company_name: string | null;
  company_interview_code: string | null;
  interview_mode: string;
  difficulty_level: string;
  status: string;
  current_turn: number;
  answered: number;
  evaluated: number;
  total_questions: number;
  integrity_score: number;
  integrity_grade: string;
  risk_level: string;
  suspicious_activity: boolean;
  tab_switch_count: number;
  ai_violations_count: number;
  total_events: number;
  critical_events: number;
  warning_events: number;
  proctor_connected: boolean;
  proctor_alive: boolean;
  proctor_heartbeat_count: number;
  last_heartbeat_gap_seconds: number | null;
  last_event_type: string | null;
  last_event_at: string | null;
  reviewer_alert: string | null;
  started_at: string | null;
  created_at: string;
};

type LiveCenterResponse = {
  company_name: string | null;
  active_sessions: LiveSession[];
  recent_sessions: LiveSession[];
};

type LiveDetailResponse = {
  session: LiveSession;
  event_feed: Array<{
    type: string;
    severity: string;
    details: string | null;
    timestamp: string | null;
  }>;
};

type AdminAnalytics = {
  total_users: number;
  total_sessions: number;
  total_revenue_rupees: number;
  average_score: number;
};

function riskTone(riskLevel: string, integrity: number) {
  if (riskLevel === "critical" || integrity < 40) {
    return { color: "#f87171", bg: "rgba(248,113,113,0.12)", border: "rgba(248,113,113,0.28)", label: "Critical" };
  }
  if (riskLevel === "elevated" || integrity < 70) {
    return { color: "#fbbf24", bg: "rgba(251,191,36,0.12)", border: "rgba(251,191,36,0.24)", label: "Elevated" };
  }
  if (riskLevel === "watch" || integrity < 90) {
    return { color: "#38bdf8", bg: "rgba(56,189,248,0.12)", border: "rgba(56,189,248,0.24)", label: "Watch" };
  }
  return { color: "#4ade80", bg: "rgba(74,222,128,0.12)", border: "rgba(74,222,128,0.24)", label: "Clear" };
}

function humanizeEvent(eventType: string | null) {
  if (!eventType) return "No event yet";
  return eventType.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

export default function ReviewerPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [dashboard, setDashboard] = useState<LiveCenterResponse | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [detail, setDetail] = useState<LiveDetailResponse | null>(null);
  const [adminAnalytics, setAdminAnalytics] = useState<AdminAnalytics | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = window.sessionStorage.getItem("reviewer_auth_token");
    if (stored) {
      setToken(stored);
    }
  }, []);

  const authHeaders = useMemo<Record<string, string>>(
    () => {
      const headers: Record<string, string> = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      return headers;
    },
    [token],
  );

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    const loadProfile = async () => {
      try {
        const res = await fetch("/api/v1/auth/profile", { headers: authHeaders });
        if (!res.ok) throw new Error("Unable to load reviewer profile.");
        const data: UserProfile = await res.json();
        if (!cancelled) setProfile(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load reviewer profile.");
          setToken("");
          window.sessionStorage.removeItem("reviewer_auth_token");
        }
      }
    };

    void loadProfile();
    return () => {
      cancelled = true;
    };
  }, [authHeaders, token]);

  useEffect(() => {
    if (!token || !profile || mustChangePassword) return;

    let cancelled = false;

    const loadDashboard = async () => {
      try {
        const liveRes = await fetch("/api/v1/enterprise/live-control-center", { headers: authHeaders });
        if (!liveRes.ok) throw new Error("Unable to load live control center.");
        const liveData: LiveCenterResponse = await liveRes.json();
        if (cancelled) return;
        setDashboard(liveData);

        const preferredSessionId = selectedSessionId || liveData.active_sessions[0]?.session_id || liveData.recent_sessions[0]?.session_id || "";
        if (preferredSessionId) {
          setSelectedSessionId(preferredSessionId);
        } else {
          setDetail(null);
        }

        if (profile.role === "super_admin") {
          const analyticsRes = await fetch("/api/v1/admin/analytics", { headers: authHeaders });
          if (analyticsRes.ok && !cancelled) {
            setAdminAnalytics(await analyticsRes.json());
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load live control center.");
        }
      }
    };

    void loadDashboard();
    const intervalId = window.setInterval(loadDashboard, 8000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [authHeaders, mustChangePassword, profile, selectedSessionId, token]);

  useEffect(() => {
    if (!token || !selectedSessionId || mustChangePassword) return;

    let cancelled = false;
    const loadDetail = async () => {
      try {
        const res = await fetch(`/api/v1/enterprise/session/${selectedSessionId}/live-control-center`, { headers: authHeaders });
        if (!res.ok) throw new Error("Unable to load interview detail.");
        const data: LiveDetailResponse = await res.json();
        if (!cancelled) setDetail(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load interview detail.");
        }
      }
    };

    void loadDetail();
    const intervalId = window.setInterval(loadDetail, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [authHeaders, mustChangePassword, selectedSessionId, token]);

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: username,
          password,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Login failed.");

      if (!["enterprise_admin", "super_admin"].includes(data.role)) {
        throw new Error("This reviewer dashboard is only for enterprise admins and super admins.");
      }

      setToken(data.access_token);
      window.sessionStorage.setItem("reviewer_auth_token", data.access_token);
      setMustChangePassword(Boolean(data.must_change_password));
      setMessage(data.must_change_password ? "Bootstrap admin must change the default password before continuing." : "Reviewer access granted.");
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch("/api/v1/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          current_password: "admin",
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Password change failed.");
      setMustChangePassword(false);
      setMessage("Password changed successfully. You can now use the live reviewer dashboard.");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password change failed.");
    } finally {
      setLoading(false);
    }
  }

  async function stopInterview(sessionId: string) {
    const reason = window.prompt("Reviewer stop reason", "Reviewer manually stopped the interview due to suspicious activity.");
    if (reason === null) return;

    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(`/api/v1/enterprise/session/${sessionId}/stop`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ reason }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Unable to stop the interview.");
      setMessage(data.message || "Interview stopped by reviewer.");
      setSelectedSessionId(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to stop the interview.");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setToken("");
    setProfile(null);
    setDashboard(null);
    setDetail(null);
    setSelectedSessionId("");
    setMustChangePassword(false);
    setMessage("");
    setError("");
    window.sessionStorage.removeItem("reviewer_auth_token");
  }

  const activeCount = dashboard?.active_sessions.length ?? 0;
  const criticalCount = dashboard?.active_sessions.filter((session) => riskTone(session.risk_level, session.integrity_score).label === "Critical").length ?? 0;
  const selectedTone = detail ? riskTone(detail.session.risk_level, detail.session.integrity_score) : null;

  if (!token) {
    return (
      <div style={shellStyle}>
        <div style={panelStyle}>
          <div style={eyebrowStyle}>Reviewer Access</div>
          <h1 style={headingStyle}>Live Anti-Cheating Review Console</h1>
          <p style={subtleStyle}>
            This view is for enterprise interviewers and platform admins. Integrity alerts stay here, not on the candidate screen.
          </p>
          <form onSubmit={handleLogin} style={{ display: "grid", gap: 14, marginTop: 24 }}>
            <Input label="Username or Email" value={username} onChange={setUsername} placeholder="admin or reviewer@company.com" />
            <Input label="Password" value={password} onChange={setPassword} placeholder="Enter password" type="password" />
            <button type="submit" style={primaryButtonStyle} disabled={loading}>
              {loading ? "Signing in..." : "Open Reviewer Dashboard"}
            </button>
          </form>
          {message && <Banner tone="success" message={message} />}
          {error && <Banner tone="error" message={error} />}
        </div>
      </div>
    );
  }

  if (mustChangePassword) {
    return (
      <div style={shellStyle}>
        <div style={panelStyle}>
          <div style={eyebrowStyle}>Secure Bootstrap</div>
          <h1 style={headingStyle}>Change The Default Admin Password</h1>
          <p style={subtleStyle}>
            The bootstrap `admin/admin` account is only valid once. Set a new password before using the reviewer console.
          </p>
          <form onSubmit={handlePasswordChange} style={{ display: "grid", gap: 14, marginTop: 24 }}>
            <Input label="New Password" value={newPassword} onChange={setNewPassword} placeholder="Enter new password" type="password" />
            <Input label="Retype Password" value={confirmPassword} onChange={setConfirmPassword} placeholder="Retype new password" type="password" />
            <button type="submit" style={primaryButtonStyle} disabled={loading}>
              {loading ? "Saving..." : "Save Password"}
            </button>
          </form>
          {message && <Banner tone="success" message={message} />}
          {error && <Banner tone="error" message={error} />}
        </div>
      </div>
    );
  }

  return (
    <div style={shellStyle}>
      <div style={{ maxWidth: 1360, margin: "0 auto", padding: "40px 20px 56px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap", marginBottom: 26 }}>
          <div>
            <div style={eyebrowStyle}>Reviewer Console</div>
            <h1 style={{ ...headingStyle, marginBottom: 10 }}>Live Anti-Cheating Control Center</h1>
            <div style={subtleStyle}>
              Signed in as {profile?.full_name} • {profile?.role.replace(/_/g, " ")}
              {profile?.company_name ? ` • ${profile.company_name}` : ""}
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button style={ghostButtonStyle} onClick={logout}>Logout</button>
          </div>
        </div>

        {criticalCount > 0 && (
          <Banner tone="error" message={`${criticalCount} live interview${criticalCount > 1 ? "s are" : " is"} in a critical integrity state. Candidate screens remain unchanged; reviewer action is required here.`} />
        )}
        {message && <Banner tone="success" message={message} />}
        {error && <Banner tone="error" message={error} />}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14, marginTop: 18, marginBottom: 22 }}>
          <MetricCard label="Active Reviews" value={String(activeCount)} hint="Scheduled, in progress, or evaluating" icon={<Activity size={16} color="#38bdf8" />} />
          <MetricCard label="Critical Alerts" value={String(criticalCount)} hint="Needs reviewer attention" icon={<ShieldAlert size={16} color="#f87171" />} />
          <MetricCard label="Recent Enterprise Sessions" value={String(dashboard?.recent_sessions.length ?? 0)} hint="Across your current scope" icon={<Shield size={16} color="#c084fc" />} />
          <MetricCard label="Platform Revenue" value={adminAnalytics ? `₹${adminAnalytics.total_revenue_rupees}` : "Restricted"} hint={adminAnalytics ? `Avg score ${adminAnalytics.average_score}` : "Visible to super admin"} icon={<ShieldCheck size={16} color="#4ade80" />} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(340px, 420px) minmax(0, 1fr)", gap: 18, alignItems: "start" }}>
          <div style={panelStyle}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
              <h2 style={sectionTitleStyle}>Live Queue</h2>
              <span style={chipStyle}>{activeCount} active</span>
            </div>
            <div style={{ display: "grid", gap: 12 }}>
              {(dashboard?.active_sessions.length ? dashboard.active_sessions : dashboard?.recent_sessions || []).map((session) => {
                const tone = riskTone(session.risk_level, session.integrity_score);
                const selected = selectedSessionId === session.session_id;
                return (
                  <button
                    key={session.session_id}
                    type="button"
                    onClick={() => setSelectedSessionId(session.session_id)}
                    style={{
                      textAlign: "left",
                      width: "100%",
                      padding: "14px 16px",
                      borderRadius: 18,
                      border: `1px solid ${selected ? tone.border : "rgba(148,163,184,0.16)"}`,
                      background: selected ? tone.bg : "rgba(9,15,29,0.74)",
                      cursor: "pointer",
                      color: "#e2e8f0",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
                      <div>
                        <div style={{ fontSize: 15, fontWeight: 800 }}>{session.candidate_name}</div>
                        <div style={{ fontSize: 12, color: "#94a3b8" }}>{session.target_role}</div>
                      </div>
                      <span style={{ ...chipStyle, color: tone.color, borderColor: tone.border, background: tone.bg }}>{tone.label}</span>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 12, color: "#cbd5e1" }}>
                      <span>Integrity: {session.integrity_score}</span>
                      <span>Status: {session.status}</span>
                      <span>Tab alerts: {session.tab_switch_count}</span>
                      <span>AI violations: {session.ai_violations_count}</span>
                    </div>
                    {session.reviewer_alert && (
                      <div style={{ marginTop: 10, fontSize: 12, color: tone.color }}>{session.reviewer_alert}</div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div style={panelStyle}>
            {detail ? (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 18 }}>
                  <div>
                    <h2 style={sectionTitleStyle}>{detail.session.candidate_name}</h2>
                    <div style={subtleStyle}>
                      {detail.session.target_role} • {detail.session.company_name || "Enterprise"} • {detail.session.candidate_email}
                    </div>
                    <div style={{ ...subtleStyle, marginTop: 6 }}>
                      Current turn {detail.session.current_turn} of {detail.session.total_questions} • last event {humanizeEvent(detail.session.last_event_type)}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <span style={{ ...chipStyle, color: selectedTone?.color, borderColor: selectedTone?.border, background: selectedTone?.bg }}>
                      Integrity {detail.session.integrity_score} • {selectedTone?.label}
                    </span>
                    <button
                      type="button"
                      onClick={() => stopInterview(detail.session.session_id)}
                      style={{ ...dangerButtonStyle, opacity: loading ? 0.7 : 1 }}
                      disabled={loading}
                    >
                      <StopCircle size={15} />
                      Stop Interview
                    </button>
                  </div>
                </div>

                {detail.session.reviewer_alert && <Banner tone="error" message={detail.session.reviewer_alert} />}

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 18 }}>
                  <MetricCard label="Warnings" value={String(detail.session.warning_events)} hint="Browser or workflow warnings" icon={<AlertTriangle size={16} color="#fbbf24" />} />
                  <MetricCard label="Critical Events" value={String(detail.session.critical_events)} hint="OS or AI integrity events" icon={<ShieldAlert size={16} color="#f87171" />} />
                  <MetricCard label="Proctor State" value={detail.session.proctor_alive ? "Live" : detail.session.proctor_connected ? "Gap detected" : "Waiting"} hint={`Heartbeats ${detail.session.proctor_heartbeat_count}`} icon={<ShieldCheck size={16} color={detail.session.proctor_alive ? "#4ade80" : "#fbbf24"} />} />
                  <MetricCard label="Answered" value={`${detail.session.answered}/${detail.session.total_questions}`} hint={`Evaluated ${detail.session.evaluated}`} icon={<Activity size={16} color="#38bdf8" />} />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 16 }}>
                  <div style={innerPanelStyle}>
                    <h3 style={miniHeadingStyle}>Event Feed</h3>
                    <div style={{ display: "grid", gap: 10 }}>
                      {detail.event_feed.length ? detail.event_feed.map((event, index) => {
                        const tone = event.severity === "critical"
                          ? { color: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.18)" }
                          : event.severity === "warning"
                            ? { color: "#fbbf24", bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.18)" }
                            : { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.18)" };
                        return (
                          <div key={`${event.type}-${event.timestamp ?? index}`} style={{ padding: "12px 14px", borderRadius: 14, background: tone.bg, border: `1px solid ${tone.border}` }}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
                              <div style={{ color: "#f8fafc", fontWeight: 700, fontSize: 13 }}>{humanizeEvent(event.type)}</div>
                              <div style={{ color: tone.color, fontWeight: 800, fontSize: 10, letterSpacing: 1, textTransform: "uppercase" }}>{event.severity}</div>
                            </div>
                            <div style={{ color: "#cbd5e1", fontSize: 12, lineHeight: 1.6 }}>{event.details || "No extra details captured."}</div>
                            <div style={{ color: "#64748b", fontSize: 11, marginTop: 4 }}>{event.timestamp ? new Date(event.timestamp).toLocaleString() : "Pending timestamp"}</div>
                          </div>
                        );
                      }) : (
                        <div style={{ color: "#94a3b8", fontSize: 13 }}>No anti-cheat events recorded yet.</div>
                      )}
                    </div>
                  </div>

                  <div style={innerPanelStyle}>
                    <h3 style={miniHeadingStyle}>Reviewer Notes</h3>
                    <div style={{ display: "grid", gap: 10, fontSize: 13, color: "#cbd5e1", lineHeight: 1.7 }}>
                      <div>Auto-warning banners are intentionally kept off the candidate screen.</div>
                      <div>Enterprise browser critical events do not hard-stop the interview automatically.</div>
                      <div>Use the manual stop button if reviewer judgment says the session should end.</div>
                      <div>Last heartbeat gap: {detail.session.last_heartbeat_gap_seconds != null ? `${detail.session.last_heartbeat_gap_seconds}s` : "No gap recorded"}.</div>
                      <div>Interview code: {detail.session.company_interview_code || "Not provided"}.</div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div style={{ color: "#94a3b8", fontSize: 14 }}>Select a session from the queue to open the reviewer control center.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
}) {
  return (
    <label style={{ display: "grid", gap: 8 }}>
      <span style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1.1 }}>{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        type={type}
        style={inputStyle}
      />
    </label>
  );
}

function Banner({ tone, message }: { tone: "error" | "success"; message: string }) {
  const palette = tone === "error"
    ? { bg: "rgba(127,29,29,0.18)", border: "rgba(248,113,113,0.28)", color: "#fecaca" }
    : { bg: "rgba(20,83,45,0.18)", border: "rgba(74,222,128,0.28)", color: "#bbf7d0" };
  return (
    <div style={{ marginTop: 14, padding: "12px 14px", borderRadius: 14, background: palette.bg, border: `1px solid ${palette.border}`, color: palette.color, fontSize: 13, lineHeight: 1.6 }}>
      {message}
    </div>
  );
}

function MetricCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
}) {
  return (
    <div style={metricCardStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, marginBottom: 10 }}>
        <span style={{ color: "#94a3b8", fontSize: 12, textTransform: "uppercase", letterSpacing: 1 }}>{label}</span>
        <span>{icon}</span>
      </div>
      <div style={{ color: "#f8fafc", fontSize: 24, fontWeight: 900, marginBottom: 4 }}>{value}</div>
      <div style={{ color: "#64748b", fontSize: 12 }}>{hint}</div>
    </div>
  );
}

const shellStyle: CSSProperties = {
  minHeight: "100vh",
  background: "radial-gradient(circle at top, rgba(56,189,248,0.12), transparent 32%), linear-gradient(180deg, #030712 0%, #020617 100%)",
  color: "#e2e8f0",
};

const panelStyle: CSSProperties = {
  background: "linear-gradient(180deg, rgba(8,15,29,0.92), rgba(5,10,22,0.96))",
  border: "1px solid rgba(148,163,184,0.16)",
  borderRadius: 24,
  padding: 24,
  boxShadow: "0 28px 80px rgba(2,6,23,0.42)",
};

const innerPanelStyle: CSSProperties = {
  background: "rgba(9,15,29,0.72)",
  border: "1px solid rgba(148,163,184,0.14)",
  borderRadius: 18,
  padding: 16,
};

const metricCardStyle: CSSProperties = {
  background: "rgba(9,15,29,0.78)",
  border: "1px solid rgba(148,163,184,0.14)",
  borderRadius: 18,
  padding: 18,
};

const headingStyle: CSSProperties = {
  fontSize: "clamp(28px, 5vw, 46px)",
  fontWeight: 900,
  lineHeight: 1.05,
  margin: 0,
};

const sectionTitleStyle: CSSProperties = {
  fontSize: 18,
  fontWeight: 800,
  margin: 0,
};

const miniHeadingStyle: CSSProperties = {
  fontSize: 14,
  fontWeight: 800,
  color: "#f8fafc",
  margin: "0 0 12px",
  textTransform: "uppercase",
  letterSpacing: 1,
};

const eyebrowStyle: CSSProperties = {
  display: "inline-block",
  marginBottom: 14,
  padding: "7px 12px",
  borderRadius: 999,
  border: "1px solid rgba(56,189,248,0.24)",
  background: "rgba(56,189,248,0.08)",
  color: "#7dd3fc",
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: 1.8,
  textTransform: "uppercase",
};

const subtleStyle: CSSProperties = {
  color: "#94a3b8",
  fontSize: 14,
  lineHeight: 1.7,
};

const inputStyle: CSSProperties = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(148,163,184,0.18)",
  background: "rgba(9,15,29,0.88)",
  color: "#f8fafc",
  padding: "13px 14px",
  fontSize: 14,
  outline: "none",
};

const chipStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid rgba(148,163,184,0.18)",
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: 1,
  textTransform: "uppercase",
};

const primaryButtonStyle: CSSProperties = {
  border: "none",
  borderRadius: 14,
  padding: "13px 18px",
  fontSize: 14,
  fontWeight: 800,
  cursor: "pointer",
  color: "#ffffff",
  background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
};

const ghostButtonStyle: CSSProperties = {
  border: "1px solid rgba(148,163,184,0.18)",
  borderRadius: 14,
  padding: "12px 16px",
  fontSize: 13,
  fontWeight: 700,
  cursor: "pointer",
  color: "#e2e8f0",
  background: "rgba(9,15,29,0.78)",
};

const dangerButtonStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  border: "1px solid rgba(248,113,113,0.28)",
  borderRadius: 14,
  padding: "12px 14px",
  fontSize: 13,
  fontWeight: 800,
  cursor: "pointer",
  color: "#fecaca",
  background: "rgba(127,29,29,0.22)",
};
