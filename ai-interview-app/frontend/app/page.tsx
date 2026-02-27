"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

/* ─── Types ───────────────────────────────────────────────── */
type InterviewMode = "mock_free" | "mock_paid" | "real";

type SessionPayload = {
  id: string;
  status: string;
  interview_mode: string;
  first_question: string;
};

type AnswerPayload = {
  score: number;
  feedback: string;
  next_question: string | null;
  status: string;
  turn_number: number;
  total_questions: number;
};

type ReportPayload = {
  session_id: string;
  status: string;
  interview_mode: string;
  answered_turns: number;
  total_questions: number;
  average_score: number;
  recommendation: string;
  generated_at: string;
};

type Eligibility = {
  eligible: boolean;
  free_mock_used: boolean;
  mock_count: number;
  real_count: number;
};

/* ─── Role Options ────────────────────────────────────────── */
const ROLE_OPTIONS = [
  "DevOps Engineer",
  "SRE / Platform Engineer",
  "Cloud Architect",
  "DevSecOps Engineer",
  "Kubernetes Specialist",
  "Full Stack Developer",
  "Data Engineer",
  "MLOps Engineer",
];

/* ─── Helper: Score color ─────────────────────────────────── */
function scoreColor(s: number) {
  if (s >= 8.5) return "#22c55e";
  if (s >= 7) return "#0ea5e9";
  if (s >= 6) return "#f59e0b";
  return "#ef4444";
}

function recommendBadge(r: string) {
  if (r === "Shortlist") return { bg: "rgba(34,197,94,0.15)", border: "rgba(34,197,94,0.4)", text: "#4ade80" };
  if (r === "Review") return { bg: "rgba(14,165,233,0.15)", border: "rgba(14,165,233,0.4)", text: "#38bdf8" };
  return { bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.35)", text: "#f87171" };
}

/* ════════════════════════════════════════════════════════════ */
export default function HomePage() {
  // ── State
  const [step, setStep] = useState<"landing" | "form" | "interview" | "report">("landing");
  const [mode, setMode] = useState<InterviewMode>("mock_free");
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [targetRole, setTargetRole] = useState(ROLE_OPTIONS[0]);
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [turnNumber, setTurnNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [lastAnswer, setLastAnswer] = useState<AnswerPayload | null>(null);
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [eligibility, setEligibility] = useState<Eligibility | null>(null);

  const canSubmit = useMemo(
    () => !!session && !!currentQuestion && answer.trim().length >= 5 && !loading,
    [session, currentQuestion, answer, loading]
  );

  /* ── Eligibility check when email changes ─────────────── */
  useEffect(() => {
    if (!candidateEmail || !candidateEmail.includes("@")) return;
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/interview/eligibility?email=${encodeURIComponent(candidateEmail)}`);
        if (res.ok) setEligibility(await res.json());
      } catch { /* ignore */ }
    }, 600);
    return () => clearTimeout(timer);
  }, [candidateEmail]);

  /* ── Auto-select mode based on eligibility ────────────── */
  useEffect(() => {
    if (eligibility?.free_mock_used && mode === "mock_free") {
      setMode("mock_paid");
    }
  }, [eligibility, mode]);

  /* ── Start session ────────────────────────────────────── */
  async function startSession(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/v1/interview/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          target_role: targetRole,
          interview_mode: mode,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to start interview session.");
      }
      const data: SessionPayload = await res.json();
      setSession(data);
      setCurrentQuestion(data.first_question);
      setTurnNumber(1);
      setAnswer("");
      setLastAnswer(null);
      setReport(null);
      setStep("interview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start session.");
    } finally {
      setLoading(false);
    }
  }

  /* ── Submit answer ────────────────────────────────────── */
  async function submitCurrentAnswer() {
    if (!session) return;
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/interview/session/${session.id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      if (!res.ok) throw new Error("Failed to submit answer.");
      const data: AnswerPayload = await res.json();
      setLastAnswer(data);
      setAnswer("");
      setTurnNumber(data.turn_number + 1);
      setTotalQuestions(data.total_questions);
      setCurrentQuestion(data.next_question ?? "");
      if (data.status === "completed") {
        const rr = await fetch(`/api/v1/interview/session/${session.id}/report`);
        if (rr.ok) setReport(await rr.json());
        setStep("report");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answer.");
    } finally {
      setLoading(false);
    }
  }

  /* ── Reset ────────────────────────────────────────────── */
  function resetAll() {
    setStep("landing");
    setSession(null);
    setCurrentQuestion("");
    setAnswer("");
    setLastAnswer(null);
    setReport(null);
    setError("");
    setTurnNumber(1);
  }

  /* ════════════════════════════════════════════════════════ */
  /*  LANDING – Mode Selection                              */
  /* ════════════════════════════════════════════════════════ */
  if (step === "landing") {
    return (
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 20px" }}>
        {/* Hero */}
        <div className="animate-fadeInUp" style={{ textAlign: "center", marginBottom: 56 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 14,
              background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 24, boxShadow: "0 0 30px rgba(14,165,233,0.3)",
            }}>
              🤖
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: 3, color: "#64748b", textTransform: "uppercase" }}>
              VAREX AI Interview
            </span>
          </div>
          <h1 style={{
            fontSize: "clamp(32px, 5vw, 56px)", fontWeight: 900, lineHeight: 1.1,
            background: "linear-gradient(135deg, #f1f5f9 0%, #38bdf8 50%, #8b5cf6 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            marginBottom: 16,
          }}>
            AI-Powered Technical<br />Interview Platform
          </h1>
          <p style={{ fontSize: 17, color: "#94a3b8", maxWidth: 600, margin: "0 auto", lineHeight: 1.7 }}>
            Practice with our AI evaluator, get instant feedback on your technical depth,
            and ace your next DevSecOps, Cloud, or SRE interview.
          </p>
        </div>

        {/* Mode Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24, marginBottom: 48 }}>
          {/* Free Mock */}
          <ModeCard
            active={mode === "mock_free"}
            disabled={eligibility?.free_mock_used ?? false}
            onClick={() => !eligibility?.free_mock_used && setMode("mock_free")}
            gradient="linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.03))"
            borderColor="rgba(16,185,129,0.3)"
            icon="🎯"
            iconBg="linear-gradient(135deg, #10b981, #059669)"
            title="Free Mock Interview"
            subtitle="Your first practice is on us"
            price="FREE"
            priceSubtext="One-time per email"
            features={["5 curated DevOps questions", "Instant AI scoring & feedback", "Performance report card"]}
            badge={eligibility?.free_mock_used ? "USED" : "RECOMMENDED"}
            badgeColor={eligibility?.free_mock_used ? "#ef4444" : "#10b981"}
          />

          {/* Paid Mock */}
          <ModeCard
            active={mode === "mock_paid"}
            disabled={false}
            onClick={() => setMode("mock_paid")}
            gradient="linear-gradient(135deg, rgba(14,165,233,0.12), rgba(14,165,233,0.03))"
            borderColor="rgba(14,165,233,0.3)"
            icon="⚡"
            iconBg="linear-gradient(135deg, #0ea5e9, #0284c7)"
            title="Paid Mock Interview"
            subtitle="Unlimited practice sessions"
            price="₹50"
            priceSubtext="Per session"
            features={["5 expert-level questions", "Detailed scoring breakdown", "Unlimited retakes", "Track improvement over sessions"]}
            badge="POPULAR"
            badgeColor="#0ea5e9"
          />

          {/* Real */}
          <ModeCard
            active={mode === "real"}
            disabled={false}
            onClick={() => setMode("real")}
            gradient="linear-gradient(135deg, rgba(139,92,246,0.12), rgba(139,92,246,0.03))"
            borderColor="rgba(139,92,246,0.3)"
            icon="🏢"
            iconBg="linear-gradient(135deg, #8b5cf6, #7c3aed)"
            title="Real Company Interview"
            subtitle="Official assessment for hiring"
            price="Enterprise"
            priceSubtext="Company-sponsored"
            features={["7 advanced scenario questions", "Production-grade evaluation", "Hiring recommendation report", "Shared with hiring manager"]}
            badge="ENTERPRISE"
            badgeColor="#8b5cf6"
          />
        </div>

        {/* CTA */}
        <div className="animate-fadeInUp delay-400" style={{ textAlign: "center" }}>
          <button
            onClick={() => setStep("form")}
            style={{
              padding: "16px 48px", borderRadius: 14, border: "none", fontWeight: 700, fontSize: 16,
              color: "#fff", cursor: "pointer",
              background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
              boxShadow: "0 4px 30px rgba(14,165,233,0.3), 0 0 60px rgba(139,92,246,0.15)",
              transition: "all 0.3s ease",
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px) scale(1.02)"; e.currentTarget.style.boxShadow = "0 8px 40px rgba(14,165,233,0.4), 0 0 80px rgba(139,92,246,0.2)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0) scale(1)"; e.currentTarget.style.boxShadow = "0 4px 30px rgba(14,165,233,0.3), 0 0 60px rgba(139,92,246,0.15)"; }}
          >
            Continue with {mode === "mock_free" ? "Free Mock" : mode === "mock_paid" ? "Paid Mock (₹50)" : "Real Interview"} →
          </button>
        </div>

        {error && <ErrorBanner message={error} onDismiss={() => setError("")} />}
      </div>
    );
  }

  /* ════════════════════════════════════════════════════════ */
  /*  FORM – Candidate Details                              */
  /* ════════════════════════════════════════════════════════ */
  if (step === "form") {
    const modeLabels: Record<InterviewMode, string> = {
      mock_free: "🎯 Free Mock Interview",
      mock_paid: "⚡ Paid Mock Interview – ₹50",
      real: "🏢 Real Company Interview",
    };

    return (
      <div style={{ maxWidth: 560, margin: "0 auto", padding: "48px 20px" }}>
        <button onClick={() => setStep("landing")} style={backBtnStyle}>
          ← Back to modes
        </button>

        <div className="animate-fadeInUp" style={cardStyle}>
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <span style={{
              display: "inline-block", padding: "6px 16px", borderRadius: 20, fontSize: 12, fontWeight: 700,
              background: mode === "mock_free" ? "rgba(16,185,129,0.12)" : mode === "mock_paid" ? "rgba(14,165,233,0.12)" : "rgba(139,92,246,0.12)",
              color: mode === "mock_free" ? "#4ade80" : mode === "mock_paid" ? "#38bdf8" : "#a78bfa",
              border: `1px solid ${mode === "mock_free" ? "rgba(16,185,129,0.3)" : mode === "mock_paid" ? "rgba(14,165,233,0.3)" : "rgba(139,92,246,0.3)"}`,
              marginBottom: 16,
            }}>
              {modeLabels[mode]}
            </span>
            <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>Candidate Details</h2>
            <p style={{ color: "#94a3b8", fontSize: 14 }}>Fill in your details to begin the assessment</p>
          </div>

          <form onSubmit={startSession} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <InputField label="Full Name" value={candidateName} onChange={setCandidateName} placeholder="John Doe" required />
            <InputField label="Email Address" type="email" value={candidateEmail} onChange={setCandidateEmail} placeholder="john@company.com" required />

            {/* Eligibility notice */}
            {eligibility?.free_mock_used && mode === "mock_free" && (
              <div style={{
                padding: "10px 14px", borderRadius: 10, fontSize: 13,
                background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.3)", color: "#fbbf24",
              }}>
                ⚠️ Free mock already used for this email. Switch to <strong>Paid Mock (₹50)</strong>.
              </div>
            )}

            {/* Role selector */}
            <div>
              <label style={labelStyle}>Target Role</label>
              <select
                value={targetRole}
                onChange={e => setTargetRole(e.target.value)}
                style={{ ...inputStyle, cursor: "pointer", appearance: "none" }}
              >
                {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            <button type="submit" disabled={loading} style={{
              ...primaryBtnStyle,
              opacity: loading ? 0.6 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}>
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                  <Spinner /> Starting Session...
                </span>
              ) : (
                "Begin Interview →"
              )}
            </button>
          </form>
        </div>

        {error && <ErrorBanner message={error} onDismiss={() => setError("")} />}
      </div>
    );
  }

  /* ════════════════════════════════════════════════════════ */
  /*  INTERVIEW – Question & Answer Flow                    */
  /* ════════════════════════════════════════════════════════ */
  if (step === "interview") {
    const progress = ((turnNumber - 1) / totalQuestions) * 100;

    return (
      <div style={{ maxWidth: 780, margin: "0 auto", padding: "32px 20px" }}>
        {/* Top bar */}
        <div className="animate-fadeIn" style={{
          display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
            }}>
              🤖
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>VAREX AI Interview</div>
              <div style={{ fontSize: 11, color: "#64748b" }}>{session?.interview_mode === "real" ? "Real Assessment" : "Mock Practice"}</div>
            </div>
          </div>
          <div style={{
            padding: "6px 14px", borderRadius: 20, fontSize: 12, fontWeight: 600,
            background: "rgba(14,165,233,0.1)", color: "#38bdf8", border: "1px solid rgba(14,165,233,0.2)",
          }}>
            Question {turnNumber > totalQuestions ? totalQuestions : turnNumber} / {totalQuestions}
          </div>
        </div>

        {/* Progress bar */}
        <div style={{
          height: 4, borderRadius: 2, background: "rgba(51,65,85,0.5)", marginBottom: 32, overflow: "hidden",
        }}>
          <div style={{
            height: "100%", borderRadius: 2, width: `${progress}%`,
            background: "linear-gradient(90deg, #0ea5e9, #8b5cf6)",
            transition: "width 0.6s ease",
          }} />
        </div>

        {/* Question Card */}
        {currentQuestion && (
          <div className="animate-fadeInUp" style={{ ...cardStyle, marginBottom: 24 }}>
            <div style={{ display: "flex", gap: 14, marginBottom: 20 }}>
              <div style={{
                flexShrink: 0, width: 40, height: 40, borderRadius: 12,
                background: "linear-gradient(135deg, rgba(14,165,233,0.2), rgba(139,92,246,0.2))",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, border: "1px solid rgba(14,165,233,0.15)",
              }}>
                💡
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
                  Question {turnNumber}
                </div>
                <p style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.6, color: "#e2e8f0" }}>
                  {currentQuestion}
                </p>
              </div>
            </div>

            <textarea
              rows={8}
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              placeholder="Type your detailed answer here… (minimum 5 characters)"
              style={{
                width: "100%", borderRadius: 12, border: "1px solid rgba(51,65,85,0.6)",
                background: "rgba(2,6,23,0.6)", color: "#f1f5f9", padding: "14px 16px",
                fontSize: 14, lineHeight: 1.7, resize: "vertical", outline: "none",
                transition: "border-color 0.3s ease",
                fontFamily: "'Inter', sans-serif",
              }}
              onFocus={e => e.target.style.borderColor = "rgba(14,165,233,0.5)"}
              onBlur={e => e.target.style.borderColor = "rgba(51,65,85,0.6)"}
            />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
              <span style={{ fontSize: 12, color: answer.length >= 5 ? "#64748b" : "#ef4444" }}>
                {answer.split(/\s+/).filter(Boolean).length} words
              </span>
              <button
                disabled={!canSubmit}
                onClick={submitCurrentAnswer}
                style={{
                  ...primaryBtnStyle,
                  padding: "12px 32px",
                  opacity: canSubmit ? 1 : 0.4,
                  cursor: canSubmit ? "pointer" : "not-allowed",
                }}
              >
                {loading ? <><Spinner /> Evaluating...</> : "Submit Answer →"}
              </button>
            </div>
          </div>
        )}

        {/* Last Answer Feedback */}
        {lastAnswer && (
          <div className="animate-slideInLeft" style={{
            ...cardStyle,
            borderColor: `${scoreColor(lastAnswer.score)}30`,
            background: `linear-gradient(135deg, ${scoreColor(lastAnswer.score)}08, transparent)`,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 14 }}>
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: `linear-gradient(135deg, ${scoreColor(lastAnswer.score)}25, ${scoreColor(lastAnswer.score)}08)`,
                display: "flex", alignItems: "center", justifyContent: "center",
                border: `1px solid ${scoreColor(lastAnswer.score)}40`,
                animation: "scoreReveal 0.5s ease-out",
              }}>
                <span style={{ fontSize: 22, fontWeight: 900, color: scoreColor(lastAnswer.score) }}>
                  {lastAnswer.score}
                </span>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: 1 }}>
                  Previous Answer Score
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#e2e8f0" }}>
                  {lastAnswer.score}/10
                </div>
              </div>
            </div>
            <p style={{ fontSize: 14, color: "#94a3b8", lineHeight: 1.7, paddingLeft: 72 }}>
              {lastAnswer.feedback}
            </p>
          </div>
        )}

        {error && <ErrorBanner message={error} onDismiss={() => setError("")} />}
      </div>
    );
  }

  /* ════════════════════════════════════════════════════════ */
  /*  REPORT – Final Evaluation                             */
  /* ════════════════════════════════════════════════════════ */
  if (step === "report" && report) {
    const badge = recommendBadge(report.recommendation);
    const pct = (report.average_score / 10) * 100;
    const circumference = 2 * Math.PI * 52;
    const offset = circumference - (pct / 100) * circumference;

    return (
      <div style={{ maxWidth: 640, margin: "0 auto", padding: "48px 20px" }}>
        <div className="animate-fadeInUp" style={{ ...cardStyle, textAlign: "center", padding: 40 }}>
          {/* Circular Score */}
          <div style={{ marginBottom: 28, position: "relative", display: "inline-block" }}>
            <svg width={128} height={128} viewBox="0 0 128 128">
              <circle cx="64" cy="64" r="52" fill="none" stroke="rgba(51,65,85,0.4)" strokeWidth="8" />
              <circle
                cx="64" cy="64" r="52" fill="none"
                stroke={scoreColor(report.average_score)}
                strokeWidth="8" strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                transform="rotate(-90 64 64)"
                style={{ transition: "stroke-dashoffset 1.5s ease", filter: `drop-shadow(0 0 8px ${scoreColor(report.average_score)}50)` }}
              />
            </svg>
            <div style={{
              position: "absolute", inset: 0, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
            }}>
              <span style={{ fontSize: 32, fontWeight: 900, color: scoreColor(report.average_score) }}>
                {report.average_score}
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>out of 10</span>
            </div>
          </div>

          <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 6 }}>Interview Complete</h2>
          <p style={{ color: "#94a3b8", fontSize: 14, marginBottom: 24 }}>
            {report.interview_mode === "real" ? "Real assessment" : "Mock practice"} • {report.answered_turns}/{report.total_questions} questions answered
          </p>

          {/* Recommendation Badge */}
          <div style={{
            display: "inline-block", padding: "10px 28px", borderRadius: 30,
            background: badge.bg, border: `1px solid ${badge.border}`, color: badge.text,
            fontWeight: 800, fontSize: 15, letterSpacing: 1,
            boxShadow: `0 0 20px ${badge.border}`,
            marginBottom: 32,
          }}>
            {report.recommendation.toUpperCase()}
          </div>

          {/* Stats */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16,
            padding: "20px 0", borderTop: "1px solid rgba(51,65,85,0.4)", borderBottom: "1px solid rgba(51,65,85,0.4)",
            marginBottom: 28,
          }}>
            <StatBox label="Questions" value={`${report.answered_turns}/${report.total_questions}`} />
            <StatBox label="Avg Score" value={`${report.average_score}/10`} />
            <StatBox label="Mode" value={report.interview_mode === "real" ? "Real" : "Mock"} />
          </div>

          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 24 }}>
            Generated: {new Date(report.generated_at).toLocaleString()}
          </p>

          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <button onClick={resetAll} style={primaryBtnStyle}>
              Take Another Interview
            </button>
            <button onClick={() => window.print()} style={{
              ...primaryBtnStyle,
              background: "rgba(51,65,85,0.5)",
              boxShadow: "none",
              border: "1px solid rgba(51,65,85,0.6)",
            }}>
              Print Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

/* ════════════════════════════════════════════════════════════ */
/*  SUB-COMPONENTS                                            */
/* ════════════════════════════════════════════════════════════ */

function ModeCard({
  active, disabled, onClick, gradient, borderColor, icon, iconBg,
  title, subtitle, price, priceSubtext, features, badge, badgeColor,
}: {
  active: boolean; disabled: boolean; onClick: () => void;
  gradient: string; borderColor: string; icon: string; iconBg: string;
  title: string; subtitle: string; price: string; priceSubtext: string;
  features: string[]; badge: string; badgeColor: string;
}) {
  return (
    <div
      onClick={disabled ? undefined : onClick}
      className="animate-fadeInUp delay-200"
      style={{
        position: "relative",
        padding: 28,
        borderRadius: 20,
        background: active ? gradient : "rgba(15,23,42,0.4)",
        border: `2px solid ${active ? borderColor : "rgba(51,65,85,0.3)"}`,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "all 0.3s ease",
        boxShadow: active ? `0 0 40px ${borderColor}` : "none",
      }}
      onMouseEnter={e => { if (!disabled && !active) e.currentTarget.style.borderColor = borderColor; }}
      onMouseLeave={e => { if (!disabled && !active) e.currentTarget.style.borderColor = "rgba(51,65,85,0.3)"; }}
    >
      {/* Badge */}
      <span style={{
        position: "absolute", top: 16, right: 16, padding: "4px 10px", borderRadius: 6,
        fontSize: 10, fontWeight: 800, letterSpacing: 1,
        background: `${badgeColor}18`, color: badgeColor, border: `1px solid ${badgeColor}40`,
      }}>
        {badge}
      </span>

      {/* Icon */}
      <div style={{
        width: 52, height: 52, borderRadius: 14, marginBottom: 16,
        background: iconBg, display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 24, boxShadow: `0 0 20px ${borderColor}`,
      }}>
        {icon}
      </div>

      <h3 style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>{title}</h3>
      <p style={{ fontSize: 13, color: "#94a3b8", marginBottom: 18 }}>{subtitle}</p>

      {/* Price */}
      <div style={{ marginBottom: 18 }}>
        <span style={{ fontSize: 32, fontWeight: 900, color: "#f1f5f9" }}>{price}</span>
        <span style={{ fontSize: 13, color: "#64748b", marginLeft: 6 }}>{priceSubtext}</span>
      </div>

      {/* Features */}
      <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        {features.map((f, i) => (
          <li key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#cbd5e1" }}>
            <span style={{ color: badgeColor, fontSize: 14 }}>✓</span>
            {f}
          </li>
        ))}
      </ul>

      {/* Selection indicator */}
      {active && (
        <div style={{
          position: "absolute", top: -1, left: -1, right: -1, bottom: -1,
          borderRadius: 20, border: `2px solid ${borderColor}`,
          pointerEvents: "none",
          animation: "pulse-glow 2s ease-in-out infinite",
        }} />
      )}
    </div>
  );
}

function InputField({ label, value, onChange, placeholder, required, type = "text" }: {
  label: string; value: string; onChange: (v: string) => void; placeholder: string; required?: boolean; type?: string;
}) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      <input
        type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} required={required}
        style={inputStyle}
        onFocus={e => e.target.style.borderColor = "rgba(14,165,233,0.5)"}
        onBlur={e => e.target.style.borderColor = "rgba(51,65,85,0.6)"}
      />
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 20, fontWeight: 800, color: "#f1f5f9" }}>{value}</div>
      <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function ErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="animate-fadeIn" style={{
      marginTop: 20, padding: "14px 18px", borderRadius: 12,
      background: "rgba(127,29,29,0.15)", border: "1px solid rgba(248,113,113,0.35)",
      color: "#fca5a5", fontSize: 14, display: "flex", justifyContent: "space-between", alignItems: "center",
    }}>
      <span>⚠️ {message}</span>
      <button onClick={onDismiss} style={{
        background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: 18, padding: "0 4px",
      }}>×</button>
    </div>
  );
}

function Spinner() {
  return (
    <span style={{
      display: "inline-block", width: 16, height: 16, borderRadius: "50%",
      border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff",
      animation: "spin 0.6s linear infinite",
    }} />
  );
}

/* ─── Shared Styles ──────────────────────────────────────── */
const cardStyle: React.CSSProperties = {
  background: "rgba(15,23,42,0.6)",
  border: "1px solid rgba(51,65,85,0.4)",
  borderRadius: 20,
  padding: 28,
  backdropFilter: "blur(12px)",
};

const labelStyle: React.CSSProperties = {
  display: "block", fontSize: 12, fontWeight: 600, color: "#94a3b8",
  marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5,
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "12px 16px", borderRadius: 12,
  border: "1px solid rgba(51,65,85,0.6)", background: "rgba(2,6,23,0.6)",
  color: "#f1f5f9", fontSize: 14, outline: "none", transition: "border-color 0.3s ease",
  fontFamily: "'Inter', sans-serif",
};

const primaryBtnStyle: React.CSSProperties = {
  padding: "14px 32px", borderRadius: 12, border: "none", fontWeight: 700, fontSize: 14,
  color: "#fff", cursor: "pointer",
  background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
  boxShadow: "0 4px 20px rgba(14,165,233,0.25)",
  transition: "all 0.3s ease",
  fontFamily: "'Inter', sans-serif",
};

const backBtnStyle: React.CSSProperties = {
  background: "none", border: "none", color: "#64748b", cursor: "pointer",
  fontSize: 13, fontWeight: 500, marginBottom: 20, padding: 0,
  transition: "color 0.2s ease",
  fontFamily: "'Inter', sans-serif",
};
