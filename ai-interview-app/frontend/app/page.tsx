"use client";

import { CSSProperties, FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Bot, Building2, Check, CircleHelp, Mic, MicOff, Volume2, VolumeX, Target, Zap } from "lucide-react";

/* ─── Types ───────────────────────────────────────────────── */
type InterviewMode = "mock_free" | "mock_paid" | "real";

type SessionPayload = {
  id: string;
  status: string;
  interview_mode: string;
  package_interviews: number;
  discount_percent: number;
  base_total_rupees: number;
  charge_rupees: number;
  payment_required: boolean;
  ai_introduction: string;
  first_question: string;
  resume_uploaded: boolean;
};

type AnswerPayload = {
  score: number;
  feedback: string;
  next_question: string | null;
  status: string;
  turn_number: number;
  total_questions: number;
  dimension_scores: Record<string, { score: number; comment: string }> | null;
  improvement_tips: string[] | null;
  strengths: string[] | null;
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
  ai_report: {
    executive_summary?: string;
    strengths?: string[];
    areas_for_improvement?: string[];
    recommendation_reason?: string;
    skill_ratings?: Record<string, number>;
    suggested_next_steps?: string;
  } | null;
};

type Eligibility = {
  eligible: boolean;
  free_mock_used: boolean;
  mock_count: number;
  real_count: number;
  next_mock_charge_rupees: number;
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
  const [step, setStep] = useState<"landing" | "form" | "intro" | "interview" | "report">("landing");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeParsedSkills, setResumeParsedSkills] = useState<string[]>([]);
  const [mode, setMode] = useState<InterviewMode>("mock_free");
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [targetRole, setTargetRole] = useState(ROLE_OPTIONS[0]);
  const [companyName, setCompanyName] = useState("");
  const [companyInterviewCode, setCompanyInterviewCode] = useState("");
  const [realInterviewCount, setRealInterviewCount] = useState(1);
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

  // ── Voice state ─────────────────────────────────────────
  const [voiceMode, setVoiceMode] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [sttSupported, setSttSupported] = useState(false);
  const [voicePhase, setVoicePhase] = useState<"speaking" | "listening" | "evaluating" | "feedback" | "idle">("idle");
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const answerBufferRef = useRef("");

  const canSubmit = useMemo(
    () => !!session && !!currentQuestion && answer.trim().length >= 5 && !loading,
    [session, currentQuestion, answer, loading]
  );

  // ── Detect Web Speech API support ──────────────────────
  useEffect(() => {
    setSpeechSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    setSttSupported(
      typeof window !== "undefined" &&
      ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)
    );
  }, []);

  // ── TTS: speak text aloud ──────────────────────────────
  const speak = useCallback((text: string, onEnd?: () => void) => {
    if (!speechSupported || !voiceMode) {
      onEnd?.();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    // Prefer a natural English voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("female"))
      || voices.find(v => v.lang.startsWith("en-") && !v.localService)
      || voices.find(v => v.lang.startsWith("en"));
    if (preferred) utterance.voice = preferred;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => { setIsSpeaking(false); onEnd?.(); };
    utterance.onerror = () => { setIsSpeaking(false); onEnd?.(); };
    window.speechSynthesis.speak(utterance);
  }, [speechSupported, voiceMode]);

  const stopSpeaking = useCallback(() => {
    if (speechSupported) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [speechSupported]);

  // ── STT: start microphone (auto-submits on silence) ────
  const startListening = useCallback(() => {
    if (!sttSupported || !voiceMode) return;
    stopSpeaking();
    setVoicePhase("listening");
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    let finalText = "";
    recognition.onresult = (event: any) => {
      let interim = "";
      for (let i = 0; i < event.results.length; i++) {
        const r = event.results[i];
        if (r.isFinal) { finalText += r[0].transcript + " "; }
        else { interim += r[0].transcript; }
      }
      answerBufferRef.current = (finalText + interim).trim();
      setAnswer(answerBufferRef.current);
      // Reset silence timer — auto-submit after 4s silence
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        recognition.stop();
      }, 4000);
    };
    recognition.onend = () => {
      setIsListening(false);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      // Auto-submit if we have enough text
      const captured = answerBufferRef.current.trim();
      if (captured.length >= 5) {
        setAnswer(captured);
        // Trigger auto-submit via a tiny delay so state settles
        setTimeout(() => {
          document.getElementById("voice-auto-submit")?.click();
        }, 200);
      } else {
        setVoicePhase("listening");
        // Restart if no meaningful answer yet
        setTimeout(() => {
          if (!recognitionRef.current) startListening();
        }, 1000);
      }
    };
    recognition.onerror = (e: any) => {
      console.warn("STT error:", e.error);
      setIsListening(false);
      if (e.error !== "aborted") {
        setTimeout(() => startListening(), 1500);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [sttSupported, voiceMode, stopSpeaking]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    setIsListening(false);
  }, []);

  // ── Auto-speak questions and start listening ───────────
  useEffect(() => {
    if (step === "interview" && currentQuestion && voiceMode && speechSupported && !loading) {
      setVoicePhase("speaking");
      answerBufferRef.current = "";
      speak(currentQuestion, () => {
        // After speaking the question, auto-start listening
        if (sttSupported && voiceMode) {
          setTimeout(() => startListening(), 400);
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuestion, step]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, [stopListening, stopSpeaking]);

  function getRealDiscountPercent(count: number) {
    if (count >= 20) return 50;
    if (count >= 10) return 30;
    if (count >= 5) return 10;
    if (count >= 2) return 5;
    return 0;
  }

  const realDiscount = getRealDiscountPercent(realInterviewCount);
  const realBaseTotal = realInterviewCount * 500;
  const realFinalPayable = Math.floor(realBaseTotal * (100 - realDiscount) / 100);

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
          company_name: mode === "real" ? companyName : undefined,
          company_interview_code: mode === "real" ? companyInterviewCode : undefined,
          package_interviews: mode === "real" ? realInterviewCount : 1,
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
      setStep("intro");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start session.");
    } finally {
      setLoading(false);
    }
  }

  /* ── Upload resume after session creation ──────────── */
  async function uploadResume() {
    if (!session || !resumeFile) return;
    setResumeUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", resumeFile);
      const res = await fetch(`/api/v1/interview/session/${session.id}/upload-resume`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to upload resume.");
      }
      const data = await res.json();
      setResumeParsedSkills(data.skills || []);

      // Regenerate introduction with resume context
      const introRes = await fetch(`/api/v1/interview/session/${session.id}/regenerate-intro`, { method: "POST" });
      if (introRes.ok) {
        const introData = await introRes.json();
        setSession(prev => prev ? {
          ...prev,
          ai_introduction: introData.ai_introduction,
          first_question: introData.first_question || prev.first_question,
          resume_uploaded: true,
        } : prev);
        if (introData.first_question) setCurrentQuestion(introData.first_question);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resume upload failed.");
    } finally {
      setResumeUploading(false);
    }
  }

  /* ── Transition from intro to actual interview ──────── */
  function beginInterview() {
    setStep("interview");
  }

  /* ── Submit answer (voice: speak feedback then auto-advance) ── */
  async function submitCurrentAnswer() {
    if (!session) return;
    stopListening();
    stopSpeaking();
    setVoicePhase("evaluating");
    setError("");
    setLoading(true);
    try {
      const submitAnswer = answer.trim() || answerBufferRef.current.trim();
      if (submitAnswer.length < 5) {
        setLoading(false);
        setVoicePhase("listening");
        setTimeout(() => startListening(), 500);
        return;
      }
      const res = await fetch(`/api/v1/interview/session/${session.id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: submitAnswer }),
      });
      if (!res.ok) throw new Error("Failed to submit answer.");
      const data: AnswerPayload = await res.json();
      setLastAnswer(data);
      setAnswer("");
      answerBufferRef.current = "";
      setTurnNumber(data.turn_number + 1);
      setTotalQuestions(data.total_questions);

      if (data.status === "completed") {
        const rr = await fetch(`/api/v1/interview/session/${session.id}/report`);
        if (rr.ok) setReport(await rr.json());
        const endMsg = data.feedback
          ? `${data.feedback}. That completes your interview. Let me generate your report.`
          : "That completes your interview. Let me generate your report.";
        setVoicePhase("feedback");
        if (voiceMode && speechSupported) {
          speak(endMsg, () => setStep("report"));
        } else {
          setStep("report");
        }
      } else {
        const feedbackText = data.feedback || "Good answer, let's move on.";
        const briefFeedback = feedbackText.length > 150
          ? feedbackText.slice(0, 150).replace(/\s+\S*$/, "") + "…"
          : feedbackText;
        setVoicePhase("feedback");
        if (voiceMode && speechSupported) {
          speak(briefFeedback, () => {
            setCurrentQuestion(data.next_question ?? "");
          });
        } else {
          setCurrentQuestion(data.next_question ?? "");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answer.");
      setVoicePhase("idle");
    } finally {
      setLoading(false);
    }
  }

  /* ── Reset ────────────────────────────────────────────── */
  function resetAll() {
    stopListening();
    stopSpeaking();
    setStep("landing");
    setSession(null);
    setCurrentQuestion("");
    setAnswer("");
    setLastAnswer(null);
    setReport(null);
    setError("");
    setTurnNumber(1);
    setResumeFile(null);
    setResumeParsedSkills([]);
  }

  /* ════════════════════════════════════════════════════════ */
  /*  LANDING – Mode Selection                              */
  /* ════════════════════════════════════════════════════════ */
  if (step === "landing") {
    const nextMockPrice = eligibility?.next_mock_charge_rupees ?? 0;
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
              <Bot size={24} color="#ffffff" aria-hidden="true" />
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

        <div className="animate-fadeInUp delay-100" style={{
          margin: "0 auto 28px",
          maxWidth: 740,
          padding: "12px 16px",
          borderRadius: 12,
          border: "1px solid rgba(14,165,233,0.28)",
          background: "linear-gradient(90deg, rgba(14,165,233,0.12), rgba(139,92,246,0.1))",
          color: "#cbd5e1",
          fontSize: 13,
          textAlign: "center",
        }}>
          Pricing: <strong>1st mock interview is complimentary</strong>. Additional practice sessions are <strong>₹50 each</strong>. Enterprise Assessment packages start at <strong>₹500/interview</strong> with volume discounts up to 50%.
          {candidateEmail && (
            <span style={{ display: "block", marginTop: 6, color: "#93c5fd" }}>
              Current email next mock charge: {nextMockPrice === 0 ? "FREE" : `₹${nextMockPrice}`}
            </span>
          )}
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
            icon={<Target size={24} color="#ffffff" aria-hidden="true" />}
            iconBg="linear-gradient(135deg, #10b981, #059669)"
            title="Practice Interview"
            subtitle="Complimentary first assessment"
            description="Get a feel for our AI evaluation engine with a free practice session. Answer 5 industry-standard DevOps & Cloud questions and receive instant scoring with actionable feedback."
            price={eligibility?.free_mock_used ? "Locked" : "FREE"}
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
            icon={<Zap size={24} color="#ffffff" aria-hidden="true" />}
            iconBg="linear-gradient(135deg, #0ea5e9, #0284c7)"
            title="Pro Practice Session"
            subtitle="Sharpen your skills, unlimited retakes"
            description="Take unlimited practice interviews to refine your answers and benchmark your growth. Each session evaluates your technical depth across real-world production scenarios with detailed feedback."
            price={eligibility?.free_mock_used ? "₹50" : "₹50 (2nd+)"}
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
            icon={<Building2 size={24} color="#ffffff" aria-hidden="true" />}
            iconBg="linear-gradient(135deg, #8b5cf6, #7c3aed)"
            title="Enterprise Assessment"
            subtitle="Official evaluation for hiring teams"
            description="Purpose-built for companies conducting structured technical hiring. Candidates face 7 advanced architecture & production scenario questions. Results include a hiring recommendation report shared directly with the hiring manager."
            price="₹500"
            priceSubtext="Per assessment · Volume discounts available"
            features={["7 advanced architecture scenarios", "Production-grade AI evaluation", "Hiring recommendation report", "Package discounts up to 50%"]}
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
            Continue with {mode === "mock_free" ? "Practice Interview" : mode === "mock_paid" ? "Pro Practice (₹50)" : "Enterprise Assessment"} →
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
      mock_free: "Practice Interview - Free",
      mock_paid: "Pro Practice Session - ₹50",
      real: "Enterprise Assessment",
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
                Free mock already used for this email. Switch to <strong>Paid Mock (₹50)</strong>.
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

            {mode === "real" && (
              <>
                <InputField
                  label="Company Name"
                  value={companyName}
                  onChange={setCompanyName}
                  placeholder="Acme Technologies Pvt Ltd"
                  required
                />
                <InputField
                  label="Interview Code"
                  value={companyInterviewCode}
                  onChange={setCompanyInterviewCode}
                  placeholder="ACME-SRE-2026-01"
                  required
                />
                <div>
                  <label style={labelStyle}>Interviews in This Package (Weekly)</label>
                  <select
                    value={realInterviewCount}
                    onChange={e => setRealInterviewCount(Number(e.target.value))}
                    style={{ ...inputStyle, cursor: "pointer", appearance: "none" }}
                  >
                    {[1, 2, 3, 4, 5, 10, 15, 20, 25, 30].map((n) => (
                      <option key={n} value={n}>
                        {n} Interview{n > 1 ? "s" : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{
                  borderRadius: 12,
                  border: "1px solid rgba(139,92,246,0.35)",
                  background: "rgba(76,29,149,0.18)",
                  padding: "12px 14px",
                  color: "#ddd6fe",
                  fontSize: 12,
                  lineHeight: 1.7,
                }}>
                  <div><strong>Enterprise Assessment Package Quote</strong></div>
                  <div>Base: ₹500 x {realInterviewCount} = ₹{realBaseTotal}</div>
                  <div>Discount: {realDiscount}%</div>
                  <div><strong>Payable: ₹{realFinalPayable}</strong></div>
                  <div style={{ color: "#c4b5fd", marginTop: 4 }}>
                    Discount slabs: 2 (5%), 5 (10%), 10 (30%), 20 (50%).
                  </div>
                </div>
                <div style={{
                  padding: "10px 14px",
                  borderRadius: 10,
                  fontSize: 12,
                  border: "1px solid rgba(139,92,246,0.3)",
                  background: "rgba(139,92,246,0.1)",
                  color: "#c4b5fd",
                }}>
                  Enterprise Assessments are designed for structured company hiring. Purchase a weekly package of interviews, assign unique codes to candidates, and receive detailed AI-powered hiring recommendation reports.
                </div>
              </>
            )}

            {mode === "mock_paid" && (
              <div style={{
                padding: "10px 14px",
                borderRadius: 10,
                fontSize: 12,
                border: "1px solid rgba(14,165,233,0.35)",
                background: "rgba(14,165,233,0.12)",
                color: "#7dd3fc",
              }}>
                This attempt is chargeable at <strong>₹50</strong>. Integrate your payment provider before enabling in production.
              </div>
            )}

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
  /*  INTRO – AI Introduction & Resume Upload               */
  /* ════════════════════════════════════════════════════════ */
  if (step === "intro" && session) {
    return (
      <div style={{ maxWidth: 680, margin: "0 auto", padding: "48px 20px" }}>
        {/* AI Interviewer Card */}
        <div className="animate-fadeInUp" style={{
          ...cardStyle, textAlign: "center", marginBottom: 24, padding: 36,
          background: "linear-gradient(135deg, rgba(14,165,233,0.08), rgba(139,92,246,0.06))",
          borderColor: "rgba(14,165,233,0.25)",
        }}>
          <div className="animate-float" style={{
            width: 88, height: 88, borderRadius: "50%", margin: "0 auto 16px",
            boxShadow: "0 0 40px rgba(14,165,233,0.3), 0 0 80px rgba(139,92,246,0.15)",
            overflow: "hidden",
          }}>
            <img src="/aria-avatar.png" alt="Aria" style={{
              width: 88, height: 88, borderRadius: "50%",
              objectFit: "cover", objectPosition: "center top",
            }} />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Meet Aria, Your AI Interviewer</h2>
          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 20 }}>Senior Technical Interviewer • VAREX AI Platform</p>

          <div style={{
            textAlign: "left", padding: "18px 20px", borderRadius: 16,
            background: "rgba(2,6,23,0.5)", border: "1px solid rgba(51,65,85,0.3)",
            fontSize: 14, lineHeight: 1.8, color: "#cbd5e1",
            fontStyle: "italic",
          }}>
            &ldquo;{session.ai_introduction}&rdquo;
          </div>
        </div>

        {/* Resume Upload */}
        <div className="animate-fadeInUp delay-200" style={{ ...cardStyle, marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Upload Your Resume <span style={{ fontSize: 12, color: "#64748b", fontWeight: 400 }}>(Optional but recommended)</span></h3>
          <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 16 }}>
            Uploading your resume helps Aria ask personalised questions based on your skills and experience.
          </p>

          <div style={{
            border: "2px dashed rgba(51,65,85,0.5)", borderRadius: 14,
            padding: "24px 16px", textAlign: "center",
            background: resumeFile ? "rgba(16,185,129,0.05)" : "rgba(2,6,23,0.3)",
            borderColor: resumeFile ? "rgba(16,185,129,0.3)" : "rgba(51,65,85,0.5)",
            transition: "all 0.3s ease",
          }}>
            {!resumeFile ? (
              <>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  id="resume-upload"
                  style={{ display: "none" }}
                  onChange={e => setResumeFile(e.target.files?.[0] || null)}
                />
                <label htmlFor="resume-upload" style={{ cursor: "pointer" }}>
                  <div style={{ display: "inline-flex", marginBottom: 8 }}><Building2 size={24} color="#93c5fd" aria-hidden="true" /></div>
                  <div style={{ fontSize: 13, color: "#94a3b8" }}>
                    Drop your resume here or <span style={{ color: "#38bdf8", textDecoration: "underline" }}>browse files</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>PDF, DOCX, or TXT • Max 5MB</div>
                </label>
              </>
            ) : (
              <div>
                <div style={{ fontSize: 14, color: "#4ade80", marginBottom: 8 }}>Resume attached: {resumeFile.name}</div>
                {!resumeParsedSkills.length && !resumeUploading && (
                  <button onClick={uploadResume} style={{ ...primaryBtnStyle, padding: "10px 24px", fontSize: 13 }}>
                    Upload & Analyse
                  </button>
                )}
                {resumeUploading && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center", color: "#38bdf8", fontSize: 13 }}>
                    <Spinner /> Parsing resume with AI...
                  </div>
                )}
                {resumeParsedSkills.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 8 }}>Detected skills:</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center" }}>
                      {resumeParsedSkills.map((s, i) => (
                        <span key={i} style={{
                          padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                          background: "rgba(14,165,233,0.12)", color: "#38bdf8", border: "1px solid rgba(14,165,233,0.2)",
                        }}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                <button onClick={() => { setResumeFile(null); setResumeParsedSkills([]); }} style={{
                  background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 11, marginTop: 8,
                }}>Remove file</button>
              </div>
            )}
          </div>
        </div>

        {/* Begin Interview CTA */}
        <div className="animate-fadeInUp delay-400" style={{ textAlign: "center" }}>
          <button onClick={() => {
            // Speak intro aloud then begin
            if (voiceMode && speechSupported && session?.ai_introduction) {
              speak(session.ai_introduction, () => beginInterview());
            } else {
              beginInterview();
            }
          }} style={{
            ...primaryBtnStyle, padding: "16px 48px", fontSize: 16,
            boxShadow: "0 4px 30px rgba(14,165,233,0.3), 0 0 60px rgba(139,92,246,0.15)",
          }}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px) scale(1.02)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0) scale(1)"; }}
          >
            {voiceMode ? "🎙 Start Voice Interview →" : "Start Answering Questions →"}
          </button>

          {/* Voice toggle */}
          {speechSupported && (
            <div style={{ marginTop: 16, display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
              <button
                onClick={() => setVoiceMode(!voiceMode)}
                style={{
                  background: voiceMode ? "rgba(14,165,233,0.12)" : "rgba(51,65,85,0.3)",
                  border: `1px solid ${voiceMode ? "rgba(14,165,233,0.3)" : "rgba(51,65,85,0.5)"}`,
                  borderRadius: 8, padding: "6px 14px", fontSize: 12, fontWeight: 600,
                  color: voiceMode ? "#38bdf8" : "#94a3b8", cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 6,
                  transition: "all 0.3s ease",
                }}
              >
                {voiceMode ? <Volume2 size={14} /> : <VolumeX size={14} />}
                {voiceMode ? "Voice Mode ON" : "Voice Mode OFF"}
              </button>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {voiceMode ? "AI will speak questions and listen to your answers" : "Text-only mode"}
              </span>
            </div>
          )}

          <p style={{ fontSize: 12, color: "#64748b", marginTop: 12 }}>
            {resumeFile && resumeParsedSkills.length > 0
              ? "Questions will be personalized based on your resume"
              : "You can still upload your resume above for personalized questions"}
          </p>
        </div>

        {error && <ErrorBanner message={error} onDismiss={() => setError("")} />}
      </div>
    );
  }

  /* ════════════════════════════════════════════════════════ */
  /*  INTERVIEW – Hands-Free Voice Agent                    */
  /* ════════════════════════════════════════════════════════ */
  if (step === "interview") {
    const progress = ((turnNumber - 1) / totalQuestions) * 100;
    const phaseLabel =
      voicePhase === "speaking" ? "Aria is asking a question…" :
        voicePhase === "listening" ? "Listening to your answer…" :
          voicePhase === "evaluating" ? "Evaluating your response…" :
            voicePhase === "feedback" ? "Aria is giving feedback…" : "";
    const phaseColor =
      voicePhase === "speaking" ? "#38bdf8" :
        voicePhase === "listening" ? "#4ade80" :
          voicePhase === "evaluating" ? "#f59e0b" :
            voicePhase === "feedback" ? "#a78bfa" : "#64748b";

    return (
      <div style={{
        minHeight: "100vh", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", padding: "20px",
        background: "radial-gradient(ellipse at 50% 30%, rgba(14,165,233,0.06) 0%, transparent 60%)",
      }}>
        {/* Hidden auto-submit trigger */}
        <button id="voice-auto-submit" onClick={submitCurrentAnswer} style={{ display: "none" }} />

        {/* Top status bar */}
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
          padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center",
          background: "rgba(2,6,23,0.85)", backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(51,65,85,0.3)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Bot size={14} color="#fff" />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0" }}>VAREX AI Interview</span>
            <span style={{ fontSize: 11, color: "#64748b" }}>
              • {session?.interview_mode === "real" ? "Enterprise" : "Practice"}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "#38bdf8" }}>
              {turnNumber > totalQuestions ? totalQuestions : turnNumber} / {totalQuestions}
            </span>
            {/* Progress bar mini */}
            <div style={{ width: 80, height: 3, borderRadius: 2, background: "rgba(51,65,85,0.5)" }}>
              <div style={{
                height: "100%", borderRadius: 2, width: `${progress}%`,
                background: "linear-gradient(90deg, #0ea5e9, #8b5cf6)",
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        </div>

        {/* Center: Human Avatar with lip-sync */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          {/* Avatar container with glow ring */}
          <div style={{
            position: "relative", width: 180, height: 180, margin: "0 auto 20px",
            animation: "ariaBreath 4s ease-in-out infinite",
          }}>
            {/* Outer glow ring */}
            <div style={{
              position: "absolute", inset: -6, borderRadius: "50%",
              background: `conic-gradient(from 0deg, ${phaseColor}40, transparent, ${phaseColor}40, transparent, ${phaseColor}40)`,
              animation: (voicePhase === "speaking" || voicePhase === "feedback")
                ? "ariaRingSpin 3s linear infinite"
                : voicePhase === "listening"
                  ? "ariaRingSpin 6s linear infinite"
                  : "none",
              opacity: voicePhase === "idle" || voicePhase === "evaluating" ? 0.3 : 0.8,
              transition: "opacity 0.5s ease",
            }} />
            {/* Inner glow */}
            <div style={{
              position: "absolute", inset: -3, borderRadius: "50%",
              boxShadow: `0 0 40px ${phaseColor}25, 0 0 80px ${phaseColor}10`,
              border: `2px solid ${phaseColor}30`,
              transition: "all 0.5s ease",
            }} />
            {/* Photo */}
            <img
              src="/aria-avatar.png"
              alt="Aria - AI Interviewer"
              style={{
                width: 180, height: 180, borderRadius: "50%",
                objectFit: "cover", objectPosition: "center top",
                position: "relative", zIndex: 2,
                filter: voicePhase === "evaluating" ? "brightness(0.8)" : "brightness(1)",
                transition: "filter 0.5s ease",
              }}
            />
            {/* Lip-sync mouth overlay - animated during speaking */}
            {(voicePhase === "speaking" || voicePhase === "feedback") && (
              <div style={{
                position: "absolute", bottom: 42, left: "50%", transform: "translateX(-50%)",
                width: 32, height: 14, borderRadius: "50%",
                background: "rgba(0,0,0,0.35)", zIndex: 3,
                animation: "ariaLipSync 0.3s ease-in-out infinite alternate",
              }} />
            )}
            {/* Eye blink overlay */}
            <div style={{
              position: "absolute", top: 62, left: 52, width: 22, height: 3,
              background: "rgba(60,40,30,0.9)", borderRadius: 2, zIndex: 3,
              animation: "ariaBlink 4s ease-in-out infinite",
              opacity: 0,
            }} />
            <div style={{
              position: "absolute", top: 62, right: 52, width: 22, height: 3,
              background: "rgba(60,40,30,0.9)", borderRadius: 2, zIndex: 3,
              animation: "ariaBlink 4s ease-in-out 0.05s infinite",
              opacity: 0,
            }} />
            {/* Phase indicator badge */}
            <div style={{
              position: "absolute", bottom: 4, right: 4, zIndex: 4,
              width: 28, height: 28, borderRadius: "50%",
              background: phaseColor, display: "flex",
              alignItems: "center", justifyContent: "center",
              border: "2px solid rgba(2,6,23,0.8)",
              boxShadow: `0 0 12px ${phaseColor}50`,
            }}>
              {voicePhase === "speaking" || voicePhase === "feedback" ? (
                <Volume2 size={13} color="#fff" />
              ) : voicePhase === "listening" ? (
                <Mic size={13} color="#fff" />
              ) : (
                <Bot size={13} color="#fff" />
              )}
            </div>
          </div>

          {/* Name */}
          <div style={{ fontSize: 18, fontWeight: 800, color: "#e2e8f0", marginBottom: 2 }}>
            Aria
          </div>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 16, letterSpacing: 0.5 }}>
            VAREX AI Interviewer
          </div>

          {/* Sound wave equalizer */}
          {(voicePhase === "speaking" || voicePhase === "listening" || voicePhase === "feedback") && (
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "center", gap: 3,
              height: 28, marginBottom: 16,
            }}>
              {Array.from({ length: 16 }).map((_, i) => (
                <div key={i} style={{
                  width: 3, borderRadius: 2,
                  background: phaseColor,
                  opacity: 0.7,
                  animation: `soundWave ${0.6 + (i % 4) * 0.15}s ease-in-out ${i * 0.06}s infinite alternate`,
                }} />
              ))}
            </div>
          )}

          {/* Phase label */}
          <div style={{
            fontSize: 14, fontWeight: 600, color: phaseColor,
            letterSpacing: 0.5, marginBottom: 8,
            transition: "all 0.3s ease",
          }}>
            {phaseLabel}
          </div>

          {voicePhase === "listening" && (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", animation: "pulse-glow 1s ease-in-out infinite" }} />
              <span style={{ fontSize: 11, color: "#f87171", fontWeight: 700, letterSpacing: 1 }}>RECORDING</span>
            </div>
          )}
        </div>

        {/* Question display */}
        {currentQuestion && (
          <div className="animate-fadeInUp" style={{
            maxWidth: 700, width: "100%",
            background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)",
            border: "1px solid rgba(51,65,85,0.4)", borderRadius: 20,
            padding: "28px 32px", textAlign: "center",
            boxShadow: `0 0 40px ${phaseColor}08`,
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700, color: "#64748b",
              textTransform: "uppercase", letterSpacing: 2, marginBottom: 12,
            }}>
              Question {turnNumber}
            </div>
            <p style={{
              fontSize: 20, fontWeight: 600, lineHeight: 1.6, color: "#e2e8f0",
              margin: 0,
            }}>
              {currentQuestion}
            </p>
          </div>
        )}

        {/* Evaluating state */}
        {voicePhase === "evaluating" && (
          <div className="animate-fadeIn" style={{
            marginTop: 24, display: "flex", alignItems: "center", gap: 10,
            padding: "12px 20px", borderRadius: 12,
            background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)",
          }}>
            <Spinner />
            <span style={{ fontSize: 13, color: "#fbbf24", fontWeight: 600 }}>
              Analyzing your response…
            </span>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 20, maxWidth: 500 }}>
            <ErrorBanner message={error} onDismiss={() => setError("")} />
          </div>
        )}

        {/* Avatar animation keyframes */}
        <style>{`
          @keyframes soundWave {
            0% { height: 3px; }
            100% { height: 24px; }
          }
          @keyframes ariaLipSync {
            0% { height: 6px; width: 28px; bottom: 44px; }
            50% { height: 14px; width: 34px; bottom: 40px; }
            100% { height: 8px; width: 30px; bottom: 43px; }
          }
          @keyframes ariaBlink {
            0%, 92%, 100% { opacity: 0; }
            95%, 97% { opacity: 1; }
          }
          @keyframes ariaBreath {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.015); }
          }
          @keyframes ariaRingSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
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
            {report.interview_mode === "real" ? "Enterprise Assessment" : "Practice Session"} • {report.answered_turns}/{report.total_questions} questions answered
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
            <StatBox label="Mode" value={report.interview_mode === "real" ? "Enterprise" : "Practice"} />
          </div>

          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 24 }}>
            Generated: {new Date(report.generated_at).toLocaleString()}
          </p>

          {/* AI Report Details (paid modes) */}
          {report.ai_report && (
            <div style={{ textAlign: "left", marginBottom: 28 }}>
              {report.ai_report.executive_summary && (
                <div style={{ marginBottom: 18, padding: "14px 16px", borderRadius: 12, background: "rgba(2,6,23,0.4)", border: "1px solid rgba(51,65,85,0.3)" }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Executive Summary</div>
                  <p style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.7 }}>{report.ai_report.executive_summary}</p>
                </div>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
                {report.ai_report.strengths && (
                  <div style={{ padding: "12px 14px", borderRadius: 12, background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.2)" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#4ade80", marginBottom: 8 }}>Strengths</div>
                    {report.ai_report.strengths.map((s, i) => (
                      <div key={i} style={{ fontSize: 12, color: "#94a3b8", marginBottom: 3 }}>• {s}</div>
                    ))}
                  </div>
                )}
                {report.ai_report.areas_for_improvement && (
                  <div style={{ padding: "12px 14px", borderRadius: 12, background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#fbbf24", marginBottom: 8 }}>Areas to Improve</div>
                    {report.ai_report.areas_for_improvement.map((a, i) => (
                      <div key={i} style={{ fontSize: 12, color: "#94a3b8", marginBottom: 3 }}>• {a}</div>
                    ))}
                  </div>
                )}
              </div>

              {report.ai_report.recommendation_reason && (
                <div style={{ marginBottom: 14, padding: "10px 14px", borderRadius: 10, background: "rgba(14,165,233,0.06)", border: "1px solid rgba(14,165,233,0.15)" }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#38bdf8", marginBottom: 4 }}>Recommendation Reason</div>
                  <p style={{ fontSize: 12, color: "#94a3b8" }}>{report.ai_report.recommendation_reason}</p>
                </div>
              )}

              {report.ai_report.suggested_next_steps && (
                <div style={{ padding: "10px 14px", borderRadius: 10, background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.15)" }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#a78bfa", marginBottom: 4 }}>Suggested Next Steps</div>
                  <p style={{ fontSize: 12, color: "#94a3b8" }}>{report.ai_report.suggested_next_steps}</p>
                </div>
              )}
            </div>
          )}

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
  title, subtitle, description, price, priceSubtext, features, badge, badgeColor,
}: {
  active: boolean; disabled: boolean; onClick: () => void;
  gradient: string; borderColor: string; icon: ReactNode; iconBg: string;
  title: string; subtitle: string; description?: string; price: string; priceSubtext: string;
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
      <p style={{ fontSize: 13, color: "#94a3b8", marginBottom: 12 }}>{subtitle}</p>

      {/* Description */}
      {description && (
        <p style={{
          fontSize: 12, color: "#64748b", lineHeight: 1.7, marginBottom: 18,
          padding: "10px 12px", borderRadius: 10,
          background: "rgba(2,6,23,0.4)", border: "1px solid rgba(51,65,85,0.25)",
        }}>
          {description}
        </p>
      )}

      {/* Price */}
      <div style={{ marginBottom: 18 }}>
        <span style={{ fontSize: 32, fontWeight: 900, color: "#f1f5f9" }}>{price}</span>
        <span style={{ fontSize: 13, color: "#64748b", marginLeft: 6 }}>{priceSubtext}</span>
      </div>

      {/* Features */}
      <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        {features.map((f, i) => (
          <li key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#cbd5e1" }}>
            <Check size={14} color={badgeColor} aria-hidden="true" />
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
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
        <AlertTriangle size={16} aria-hidden="true" />
        {message}
      </span>
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
const cardStyle: CSSProperties = {
  background: "rgba(15,23,42,0.6)",
  border: "1px solid rgba(51,65,85,0.4)",
  borderRadius: 20,
  padding: 28,
  backdropFilter: "blur(12px)",
};

const labelStyle: CSSProperties = {
  display: "block", fontSize: 12, fontWeight: 600, color: "#94a3b8",
  marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5,
};

const inputStyle: CSSProperties = {
  width: "100%", padding: "12px 16px", borderRadius: 12,
  border: "1px solid rgba(51,65,85,0.6)", background: "rgba(2,6,23,0.6)",
  color: "#f1f5f9", fontSize: 14, outline: "none", transition: "border-color 0.3s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
};

const primaryBtnStyle: CSSProperties = {
  padding: "14px 32px", borderRadius: 12, border: "none", fontWeight: 700, fontSize: 14,
  color: "#fff", cursor: "pointer",
  background: "linear-gradient(135deg, #0ea5e9, #8b5cf6)",
  boxShadow: "0 4px 20px rgba(14,165,233,0.25)",
  transition: "all 0.3s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
};

const backBtnStyle: CSSProperties = {
  background: "none", border: "none", color: "#64748b", cursor: "pointer",
  fontSize: 13, fontWeight: 500, marginBottom: 20, padding: 0,
  transition: "color 0.2s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
};
