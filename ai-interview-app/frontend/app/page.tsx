"use client";

import Link from "next/link";
import { CSSProperties, FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Activity, AlertTriangle, Bot, Building2, Check, CircleHelp, Eye, Mic, MicOff, ShieldAlert, ShieldCheck, Volume2, VolumeX, Target, Zap } from "lucide-react";

/* ─── Types ───────────────────────────────────────────────── */
type InterviewMode = "mock_free" | "mock_paid" | "real";

type SessionPayload = {
  id: string;
  session_token: string;
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
  anti_cheat_summary?: {
    tab_switches: number;
    ai_violations: number;
    integrity_score: number;
    suspicious: boolean;
    proctor_was_connected: boolean;
    proctor_heartbeats: number;
  } | null;
};

type SessionStatusPayload = {
  session_id: string;
  status: string;
  total_questions: number;
  answered: number;
  evaluated: number;
  all_evaluated: boolean;
  timer: {
    expired: boolean;
    elapsed_seconds?: number;
    remaining_seconds?: number;
  };
  suspicious_activity: boolean;
  tab_switch_count: number;
  ai_violations_count: number;
  integrity_score: number;
  proctor_connected: boolean;
  proctor_heartbeat_count: number;
};

type AntiCheatSummaryPayload = {
  session_id: string;
  tab_switch_count: number;
  proctor_connected: boolean;
  proctor_heartbeat_count: number;
  proctor_environment: Record<string, unknown> | null;
  ai_violations_count: number;
  integrity_score: number;
  integrity_grade: string;
  risk_level?: string;
  suspicious: boolean;
  total_events: number;
  critical_events: number;
  warning_events: number;
  browser_alerts?: number;
  recent_event_type?: string | null;
  recent_event_at?: string | null;
  events: Array<{
    type: string;
    severity: string;
    details: string | null;
    timestamp: string | null;
  }>;
};

type ProctorHealthPayload = {
  proctor_connected: boolean;
  proctor_alive: boolean;
  heartbeat_count: number;
  last_heartbeat_gap_seconds: number | null;
  integrity_score: number;
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

function antiCheatTone(score: number, suspicious: boolean) {
  if (score < 40) return { label: "Critical", color: "#f87171", glow: "rgba(248,113,113,0.25)" };
  if (suspicious || score < 70) return { label: "Elevated", color: "#fbbf24", glow: "rgba(251,191,36,0.22)" };
  if (score < 90) return { label: "Watch", color: "#38bdf8", glow: "rgba(56,189,248,0.22)" };
  return { label: "Clear", color: "#4ade80", glow: "rgba(74,222,128,0.2)" };
}

function formatAntiCheatEvent(type: string) {
  return type.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

/* ════════════════════════════════════════════════════════════ */
export default function HomePage() {
  const searchParams = useSearchParams();
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
  const [verificationMessage, setVerificationMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<SessionStatusPayload | null>(null);
  const [antiCheatSummary, setAntiCheatSummary] = useState<AntiCheatSummaryPayload | null>(null);
  const [proctorHealth, setProctorHealth] = useState<ProctorHealthPayload | null>(null);
  const [localEventFeed, setLocalEventFeed] = useState<Array<{ type: string; details: string; at: number }>>([]);

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
  const forceSubmitRef = useRef(false);
  const forceAdvanceRef = useRef(false);
  const antiCheatDedupRef = useRef<Record<string, number>>({});

  const canSubmit = useMemo(
    () => !!session && !!currentQuestion && answer.trim().length >= 5 && !loading,
    [session, currentQuestion, answer, loading]
  );

  const resolvedInterviewMode = mode === "real" ? "enterprise" : mode;

  const sessionHeaders = useMemo<Record<string, string>>(
    () => {
      const headers: Record<string, string> = {};
      if (session) {
        headers["X-Interview-Token"] = session.session_token;
      }
      return headers;
    },
    [session]
  );

  const pushLocalEvent = useCallback((type: string, details: string) => {
    setLocalEventFeed((prev) => [
      { type, details, at: Date.now() },
      ...prev,
    ].slice(0, 8));
  }, []);

  const postAntiCheatEvent = useCallback(async (
    eventType: "tab_switch" | "window_blur" | "copy_paste" | "right_click" | "devtools_shortcut" | "print_attempt",
    details: string,
  ) => {
    if (!session) return;

    const dedupKey = `${eventType}:${details}`;
    const now = Date.now();
    const lastSent = antiCheatDedupRef.current[dedupKey] ?? 0;
    if (now - lastSent < 4000) {
      return;
    }
    antiCheatDedupRef.current[dedupKey] = now;

    pushLocalEvent(eventType, details);
    try {
      const res = await fetch(`/api/v1/interview/session/${session.id}/anti-cheat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...sessionHeaders,
        },
        body: JSON.stringify({
          event_type: eventType,
          details,
        }),
      });
      if (!res.ok) return;
      await res.json();
    } catch {
      // Keep interview flow uninterrupted if event logging fails.
    }
  }, [pushLocalEvent, session, sessionHeaders]);

  // ── Detect Web Speech API support ──────────────────────
  useEffect(() => {
    setSpeechSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    setSttSupported(
      typeof window !== "undefined" &&
      ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)
    );
    // Preload voices (Chrome loads them async)
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  }, []);

  useEffect(() => {
    const verifyToken = searchParams.get("verify_token");
    if (!verifyToken) return;

    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/v1/auth/verify-email?token=${encodeURIComponent(verifyToken)}`);
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        if (res.ok) {
          setVerificationMessage("Email verified successfully. You can continue with additional mock interviews.");
        } else {
          setVerificationMessage(data.message || "Verification link is invalid or expired.");
        }
      } catch {
        if (!cancelled) {
          setVerificationMessage("Unable to verify your email right now. Please try again.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  // ── Find best female English voice ─────────────────────
  const pickFemaleVoice = useCallback(() => {
    const voices = window.speechSynthesis.getVoices();
    const enVoices = voices.filter(v => v.lang.startsWith("en"));
    // Known female voice names across platforms — Samantha first
    const femaleNames = ["samantha", "zira", "heera", "karen", "moira", "fiona",
      "victoria", "susan", "hazel", "linda", "catherine", "tessa",
      "google uk english female", "google us english", "female"];
    // Priority 0: Samantha specifically
    const samantha = enVoices.find(v => v.name.toLowerCase().includes("samantha"));
    if (samantha) return samantha;
    // Priority 1: other known female names
    const byName = enVoices.find(v => femaleNames.some(n => v.name.toLowerCase().includes(n)));
    if (byName) return byName;
    // Priority 2: cloud/remote female voice
    const remote = enVoices.find(v => !v.localService);
    if (remote) return remote;
    // Priority 3: any English voice
    return enVoices[0] || voices[0] || null;
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
    utterance.pitch = 1.1;
    utterance.volume = 1.0;
    const voice = pickFemaleVoice();
    if (voice) utterance.voice = voice;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => { setIsSpeaking(false); onEnd?.(); };
    utterance.onerror = () => { setIsSpeaking(false); onEnd?.(); };
    window.speechSynthesis.speak(utterance);
  }, [speechSupported, voiceMode, pickFemaleVoice]);

  const stopSpeaking = useCallback(() => {
    if (speechSupported) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [speechSupported]);

  // ── Trigger phrases that signal "I'm done answering" ────
  const STOP_PHRASES = [
    "done", "i'm done", "i am done", "that's all", "that is all",
    "that's it", "that is it", "completed", "finished", "i'm finished",
    "next question", "move on", "go ahead", "next please", "that's my answer",
    "over", "end", "thank you", "thanks",
  ];

  // ── STT: start microphone (auto-submits on silence or trigger word) ──
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
    let triggerDetected = false;

    recognition.onresult = (event: any) => {
      if (triggerDetected) return;
      let interim = "";
      let latestFinal = "";
      for (let i = 0; i < event.results.length; i++) {
        const r = event.results[i];
        if (r.isFinal) {
          const chunk = r[0].transcript;
          finalText += chunk + " ";
          latestFinal = chunk;
        } else {
          interim += r[0].transcript;
        }
      }
      const fullText = (finalText + interim).trim();

      // Check trigger words ONLY on finalized speech (not interim)
      if (latestFinal) {
        const lowerFinal = latestFinal.toLowerCase().trim();
        const lowerFull = finalText.toLowerCase().trim();
        // Check if the latest finalized chunk ends with a trigger phrase
        const matchedTrigger = STOP_PHRASES.find(phrase =>
          lowerFinal === phrase ||
          lowerFinal.endsWith(" " + phrase) ||
          lowerFinal.endsWith("." + phrase) ||
          lowerFinal.endsWith(", " + phrase)
        );

        if (matchedTrigger) {
          triggerDetected = true;
          // Strip trigger phrase from the full answer
          const escapedTrigger = matchedTrigger.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
          const cleanAnswer = finalText.replace(
            new RegExp(`[\\s.,]*${escapedTrigger}[\\s.]*$`, "i"), ""
          ).trim();
          answerBufferRef.current = cleanAnswer || finalText.trim();
          setAnswer(answerBufferRef.current);
          forceSubmitRef.current = true;
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          recognition.stop();
          return;
        }
      }

      answerBufferRef.current = fullText;
      setAnswer(answerBufferRef.current);

      // Reset silence timer — auto-submit after 3.5s silence
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        recognition.stop();
      }, 3500);
    };
    recognition.onend = () => {
      setIsListening(false);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null;
      }
      // Auto-submit if we have enough text
      const captured = answerBufferRef.current.trim();
      const shouldForceSubmit = forceSubmitRef.current;
      forceSubmitRef.current = false;
      if (captured.length >= 5 || (shouldForceSubmit && captured.length >= 1)) {
        if (shouldForceSubmit) {
          forceAdvanceRef.current = true;
        }
        setAnswer(captured);
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
    forceSubmitRef.current = false;
    forceAdvanceRef.current = false;
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

  useEffect(() => {
    if (step !== "interview" || !session) return;

    let cancelled = false;

    const syncAntiCheat = async () => {
      try {
        const [statusRes, summaryRes, proctorRes] = await Promise.all([
          fetch(`/api/v1/interview/session/${session.id}/status`, { headers: sessionHeaders }),
          fetch(`/api/v1/interview/session/${session.id}/anti-cheat`, { headers: sessionHeaders }),
          fetch(`/api/v1/interview/session/${session.id}/proctor-health`, { headers: sessionHeaders }),
        ]);

        if (cancelled) return;

        if (statusRes.ok) {
          const data: SessionStatusPayload = await statusRes.json();
          if (!cancelled) setSessionStatus(data);
        }
        if (summaryRes.ok) {
          const data: AntiCheatSummaryPayload = await summaryRes.json();
          if (!cancelled) setAntiCheatSummary(data);
        }
        if (proctorRes.ok) {
          const data: ProctorHealthPayload = await proctorRes.json();
          if (!cancelled) setProctorHealth(data);
        }
      } catch {
        // Live telemetry should never interrupt the interview itself.
      }
    };

    void syncAntiCheat();
    const intervalId = window.setInterval(syncAntiCheat, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [session, sessionHeaders, step]);

  useEffect(() => {
    if (step !== "interview" || !session) return;

    const onVisibilityChange = () => {
      if (document.hidden) {
        void postAntiCheatEvent("tab_switch", "Candidate moved away from the active interview tab.");
      }
    };

    const onWindowBlur = () => {
      void postAntiCheatEvent("window_blur", "Browser window lost focus during the interview.");
    };

    const onCopy = () => {
      void postAntiCheatEvent("copy_paste", "Copy action detected during the interview.");
    };

    const onPaste = () => {
      void postAntiCheatEvent("copy_paste", "Paste action detected during the interview.");
    };

    const onContextMenu = () => {
      void postAntiCheatEvent("right_click", "Right-click context menu opened during the interview.");
    };

    const onKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const ctrlOrMeta = event.ctrlKey || event.metaKey;
      const devToolsShortcut =
        key === "f12"
        || (ctrlOrMeta && event.shiftKey && ["i", "j", "c"].includes(key))
        || (ctrlOrMeta && key === "u");
      const printShortcut = ctrlOrMeta && key === "p";

      if (devToolsShortcut) {
        void postAntiCheatEvent("devtools_shortcut", "Developer-tools shortcut detected during the interview.");
      }

      if (printShortcut) {
        void postAntiCheatEvent("print_attempt", "Print or save shortcut detected during the interview.");
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("blur", onWindowBlur);
    document.addEventListener("copy", onCopy);
    document.addEventListener("paste", onPaste);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener("blur", onWindowBlur);
      document.removeEventListener("copy", onCopy);
      document.removeEventListener("paste", onPaste);
      document.removeEventListener("contextmenu", onContextMenu);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [postAntiCheatEvent, session, step]);

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
          interview_mode: resolvedInterviewMode,
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
      setSessionStatus(null);
      setAntiCheatSummary(null);
      setProctorHealth(null);
      setLocalEventFeed([]);
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
        headers: sessionHeaders,
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to upload resume.");
      }
      const data = await res.json();
      setResumeParsedSkills(data.skills || []);

      // Regenerate introduction with resume context
      const introRes = await fetch(`/api/v1/interview/session/${session.id}/regenerate-intro`, {
        method: "POST",
        headers: sessionHeaders,
      });
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
      const forcedAdvance = forceAdvanceRef.current;
      forceAdvanceRef.current = false;
      const submitAnswer = answer.trim() || answerBufferRef.current.trim();
      if (submitAnswer.length < 5 && !forcedAdvance) {
        setLoading(false);
        setVoicePhase("listening");
        setTimeout(() => startListening(), 500);
        return;
      }
      if (submitAnswer.length < 1) {
        setLoading(false);
        setVoicePhase("listening");
        setTimeout(() => startListening(), 500);
        return;
      }
      const res = await fetch(`/api/v1/interview/session/${session.id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...sessionHeaders },
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
        const rr = await fetch(`/api/v1/interview/session/${session.id}/report`, {
          headers: sessionHeaders,
        });
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
    setVerificationMessage(null);
    setTurnNumber(1);
    setResumeFile(null);
    setResumeParsedSkills([]);
    setSessionStatus(null);
    setAntiCheatSummary(null);
    setProctorHealth(null);
    setLocalEventFeed([]);
  }

  /* ════════════════════════════════════════════════════════ */
  /*  LANDING – Mode Selection                              */
  /* ════════════════════════════════════════════════════════ */
  if (step === "landing") {
    return (
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "48px 20px", position: "relative" }}>
        <div className="orbital-grid" style={{ position: "absolute", inset: 0, pointerEvents: "none" }} />
        <div className="chromatic-orbit" style={{ position: "absolute", top: 80, left: -40, width: 320, height: 320, pointerEvents: "none" }} />
        <div className="chromatic-orbit" style={{ position: "absolute", top: 120, right: -30, width: 280, height: 280, pointerEvents: "none" }} />
        <div className="signal-beam" style={{ position: "absolute", inset: "18% 8% auto 18%", height: 240, pointerEvents: "none" }} />
        <svg
          className="absolute inset-0 pointer-events-none opacity-45"
          viewBox="0 0 1200 900"
          fill="none"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path d="M92 186H420C468 186 506 224 506 272V314" stroke="rgba(56,189,248,0.22)" strokeWidth="1.2" strokeDasharray="7 10" />
          <path d="M1108 198H786C724 198 680 242 680 304V382" stroke="rgba(167,139,250,0.22)" strokeWidth="1.2" strokeDasharray="7 10" />
          <path d="M184 628H420C508 628 578 558 578 470V426" stroke="rgba(244,63,94,0.16)" strokeWidth="1.1" strokeDasharray="6 12" />
          <path d="M1024 646H814C728 646 660 578 660 492V430" stroke="rgba(34,211,238,0.18)" strokeWidth="1.1" strokeDasharray="6 12" />
          <circle cx="506" cy="314" r="4" fill="rgba(56,189,248,0.72)" />
          <circle cx="680" cy="382" r="4" fill="rgba(167,139,250,0.74)" />
          <circle cx="578" cy="426" r="3.5" fill="rgba(244,63,94,0.66)" />
          <circle cx="660" cy="430" r="3.5" fill="rgba(34,211,238,0.68)" />
        </svg>
        <div className="animate-fadeInUp" style={{ display: "flex", justifyContent: "flex-end", marginBottom: 18 }}>
          <Link
            href="/reviewer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 14px",
              borderRadius: 999,
              border: "1px solid rgba(248,113,113,0.26)",
              background: "rgba(127,29,29,0.16)",
              color: "#fecaca",
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: 1,
              textTransform: "uppercase",
              textDecoration: "none",
              boxShadow: "0 10px 24px rgba(127,29,29,0.16)",
            }}
          >
            <ShieldAlert size={14} />
            Reviewer Console
          </Link>
        </div>
        {/* Hero */}
        <div className="animate-fadeInUp" style={{ textAlign: "center", marginBottom: 56 }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 14px",
            borderRadius: 999,
            marginBottom: 18,
            border: "1px solid rgba(167,139,250,0.26)",
            background: "rgba(16,16,37,0.72)",
            color: "#d8ccff",
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: 2.2,
            textTransform: "uppercase",
          }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f43f5e", boxShadow: "0 0 18px rgba(244,63,94,0.65)" }} />
            Spatial Interview Experience
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 10,
            maxWidth: 560,
            margin: "0 auto 22px",
          }}>
            {[
              { label: "Inference Engine", value: "Live" },
              { label: "Integrity Mesh", value: "Active" },
              { label: "Report Pipeline", value: "Ready" },
            ].map((item) => (
              <div
                key={item.label}
                className="spatial-panel"
                style={{
                  padding: "12px 14px",
                  borderRadius: 16,
                  textAlign: "left",
                }}
              >
                <div style={{ fontSize: 10, color: "#8ea0c3", textTransform: "uppercase", letterSpacing: 1.4, marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: "#eef2ff" }}>{item.value}</div>
              </div>
            ))}
          </div>
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
              First mock is open. To continue with another personal mock, that email must be verified.
            </span>
          )}
        </div>

        <div className="animate-fadeInUp delay-100 spatial-panel depth-ring" style={{
          margin: "0 auto 26px",
          maxWidth: 820,
          padding: "16px 18px",
          borderRadius: 18,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: 12,
        }}>
          {[
            "Adaptive question sequencing",
            "Voice-first candidate experience",
            "Instant scoring & report synthesis",
            "Live anti-cheat reviewer telemetry",
          ].map((item) => (
            <div key={item} style={{
              padding: "10px 12px",
              borderRadius: 12,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#dbeafe",
              fontSize: 12,
              lineHeight: 1.6,
            }}>
              {item}
            </div>
          ))}
        </div>

        {verificationMessage && (
          <div className="animate-fadeInUp delay-150" style={{
            margin: "0 auto 24px",
            maxWidth: 740,
            padding: "12px 16px",
            borderRadius: 12,
            border: "1px solid rgba(16,185,129,0.28)",
            background: "rgba(16,185,129,0.08)",
            color: "#bbf7d0",
            fontSize: 13,
            textAlign: "center",
          }}>
            {verificationMessage}
          </div>
        )}

        <div className="animate-fadeInUp delay-150" style={{
          margin: "0 auto 30px",
          maxWidth: 740,
          padding: "12px 16px",
          borderRadius: 12,
          border: "1px solid rgba(248,113,113,0.22)",
          background: "linear-gradient(90deg, rgba(127,29,29,0.18), rgba(30,41,59,0.18))",
          color: "#fecaca",
          fontSize: 13,
          textAlign: "center",
          lineHeight: 1.6,
        }}>
          Interviewers and enterprise reviewers can monitor live anti-cheat telemetry from the{" "}
          <Link href="/reviewer" style={{ color: "#fda4af", fontWeight: 800, textDecoration: "none" }}>
            Reviewer Console
          </Link>.
        </div>

        {/* Mode Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24, marginBottom: 48 }}>
          {/* Free Mock */}
          <ModeCard
            active={mode === "mock_free"}
            disabled={false}
            onClick={() => setMode("mock_free")}
            gradient="linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.03))"
            borderColor="rgba(16,185,129,0.3)"
            icon={<Target size={24} color="#ffffff" aria-hidden="true" />}
            iconBg="linear-gradient(135deg, #10b981, #059669)"
            title="Practice Interview"
            subtitle="Complimentary first assessment"
            description="Get a feel for our AI evaluation engine with a free practice session. Answer 5 industry-standard DevOps & Cloud questions and receive instant scoring with actionable feedback."
            price="FREE"
            priceSubtext="One-time per email"
            features={["5 curated DevOps questions", "Instant AI scoring & feedback", "Performance report card"]}
            badge="RECOMMENDED"
            badgeColor="#10b981"
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

        <div className="animate-fadeInUp spatial-panel depth-ring" style={cardStyle}>
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

            {mode !== "real" && (
              <div style={{
                padding: "10px 14px", borderRadius: 10, fontSize: 13,
                background: "rgba(14,165,233,0.08)", border: "1px solid rgba(14,165,233,0.22)", color: "#bae6fd",
              }}>
                First personal mock works without verification. If you continue with another personal interview later, we will send a verification link to this email.
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
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "48px 20px", position: "relative" }}>
        <div className="chromatic-orbit" style={{ position: "absolute", top: 18, left: -60, width: 220, height: 220, pointerEvents: "none" }} />
        <div className="signal-beam" style={{ position: "absolute", inset: "8% 12% auto 12%", height: 220, pointerEvents: "none" }} />
        {/* AI Interviewer Card */}
        <div className="animate-fadeInUp" style={{
          ...cardStyle, textAlign: "center", marginBottom: 24, padding: 36,
          background: "linear-gradient(135deg, rgba(14,165,233,0.08), rgba(139,92,246,0.06))",
          borderColor: "rgba(14,165,233,0.25)",
        }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 10,
            marginBottom: 20,
          }}>
            {[
              { label: "Interviewer", value: "Aria" },
              { label: "Voice Layer", value: voiceMode ? "Enabled" : "Manual" },
              { label: "Session State", value: session.resume_uploaded ? "Contextualized" : "Primed" },
            ].map((item) => (
              <div
                key={item.label}
                style={{
                  padding: "10px 12px",
                  borderRadius: 14,
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  textAlign: "left",
                }}
              >
                <div style={{ fontSize: 10, color: "#93c5fd", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 15, fontWeight: 800, color: "#f8fafc" }}>{item.value}</div>
              </div>
            ))}
          </div>
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
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 10,
            marginBottom: 16,
          }}>
            {[
              "Resume summarization",
              "Skill extraction",
              "Question tailoring",
              "Intro regeneration",
            ].map((item) => (
              <div key={item} style={{
                padding: "9px 12px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.08)",
                background: "rgba(255,255,255,0.03)",
                color: "#cbd5e1",
                fontSize: 12,
              }}>
                {item}
              </div>
            ))}
          </div>

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
    const integrityScore = antiCheatSummary?.integrity_score ?? sessionStatus?.integrity_score ?? proctorHealth?.integrity_score ?? 100;
    const suspiciousState = antiCheatSummary?.suspicious ?? sessionStatus?.suspicious_activity ?? false;
    const tone = antiCheatTone(integrityScore, suspiciousState);
    const recentEvents = antiCheatSummary?.events.slice(-5).reverse() ?? [];
    const remainingMinutes = sessionStatus?.timer.remaining_seconds != null
      ? Math.max(0, Math.ceil(sessionStatus.timer.remaining_seconds / 60))
      : null;

    return (
      <div style={{
        position: "relative",
        overflow: "hidden",
        minHeight: "100vh", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", padding: "20px",
        background: "radial-gradient(ellipse at 50% 24%, rgba(37,99,235,0.1) 0%, transparent 62%), linear-gradient(180deg, rgba(9,14,28,0.14), rgba(9,14,28,0.04))",
      }}>
        <div
          className="chromatic-orbit"
          style={{
            position: "absolute",
            top: 110,
            left: -70,
            width: 280,
            height: 280,
            pointerEvents: "none",
            opacity: 0.45,
          }}
        />
        <div
          className="chromatic-orbit"
          style={{
            position: "absolute",
            right: -40,
            bottom: 120,
            width: 250,
            height: 250,
            pointerEvents: "none",
            opacity: 0.4,
            animationDelay: "4s",
          }}
        />
        <div
          className="signal-beam"
          style={{
            position: "absolute",
            inset: "22% 12% auto 16%",
            height: 240,
            pointerEvents: "none",
            opacity: 0.32,
          }}
        />
        <div
          className="orbital-grid"
          style={{
            position: "absolute",
            inset: "12% 10% 8%",
            pointerEvents: "none",
            opacity: 0.18,
          }}
        />
        <svg
          className="telemetry-mesh"
          viewBox="0 0 1440 900"
          preserveAspectRatio="none"
          aria-hidden="true"
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
            opacity: 0.34,
          }}
        >
          <defs>
            <linearGradient id="interviewMeshA" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(34,211,238,0)" />
              <stop offset="48%" stopColor="rgba(34,211,238,0.32)" />
              <stop offset="100%" stopColor="rgba(167,139,250,0)" />
            </linearGradient>
            <linearGradient id="interviewMeshB" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(244,63,94,0)" />
              <stop offset="52%" stopColor="rgba(244,63,94,0.22)" />
              <stop offset="100%" stopColor="rgba(56,189,248,0)" />
            </linearGradient>
          </defs>
          <path d="M64 212C186 212 248 154 370 154C492 154 588 262 718 262C848 262 912 176 1030 176C1156 176 1244 246 1374 246" stroke="url(#interviewMeshA)" strokeWidth="1.4" />
          <path d="M118 612C242 612 316 544 432 544C566 544 622 652 760 652C900 652 968 572 1088 572C1206 572 1288 632 1396 632" stroke="url(#interviewMeshB)" strokeWidth="1.25" />
          <path d="M252 114L382 154L522 228L718 262L896 220L1030 176L1188 198" stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
          <path d="M214 706L432 544L652 584L760 652L972 604L1172 648" stroke="rgba(148,163,184,0.1)" strokeWidth="1" />
          <circle cx="382" cy="154" r="4" fill="rgba(56,189,248,0.62)" />
          <circle cx="718" cy="262" r="4.5" fill="rgba(167,139,250,0.55)" />
          <circle cx="1030" cy="176" r="4" fill="rgba(34,211,238,0.54)" />
          <circle cx="432" cy="544" r="4" fill="rgba(244,63,94,0.46)" />
          <circle cx="760" cy="652" r="4.5" fill="rgba(56,189,248,0.48)" />
          <circle cx="1088" cy="572" r="4" fill="rgba(167,139,250,0.46)" />
        </svg>

        {/* Hidden auto-submit trigger */}
        <button id="voice-auto-submit" onClick={submitCurrentAnswer} style={{ display: "none" }} />

        {/* Top status bar */}
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
          padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center",
          background: "rgba(255,255,255,0.86)", backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(148,163,184,0.18)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Bot size={14} color="#fff" />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#15304b" }}>VAREX AI Interview</span>
            <span style={{ fontSize: 11, color: "#5d728a" }}>
              • {session?.interview_mode === "enterprise" ? "Enterprise" : "Practice"}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{
              padding: "5px 10px",
              borderRadius: 999,
              border: `1px solid ${tone.glow}`,
              background: tone.glow,
              color: tone.color,
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 0.5,
            }}>
              Integrity {integrityScore} • {tone.label}
            </span>
            <span style={{ fontSize: 12, fontWeight: 600, color: "#2563eb" }}>
              {turnNumber > totalQuestions ? totalQuestions : turnNumber} / {totalQuestions}
            </span>
            {/* Progress bar mini */}
            <div style={{ width: 80, height: 3, borderRadius: 2, background: "rgba(191,219,254,0.9)" }}>
              <div style={{
                height: "100%", borderRadius: 2, width: `${progress}%`,
                background: "linear-gradient(90deg, #2563eb, #f97316)",
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        </div>

        <div className="animate-fadeInUp" style={{
          width: "100%",
          maxWidth: 1120,
          marginTop: 74,
          marginBottom: 20,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 18,
          alignItems: "stretch",
        }}>
          <div className="spatial-panel" style={{
            padding: "18px 20px",
            borderRadius: 22,
            border: "1px solid rgba(56,189,248,0.16)",
            background: "linear-gradient(140deg, rgba(10,18,38,0.88), rgba(12,23,46,0.72))",
            boxShadow: "0 24px 70px rgba(2,6,23,0.4)",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginBottom: 18, flexWrap: "wrap" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <ShieldAlert size={18} color={tone.color} />
                  <span style={{ fontSize: 12, fontWeight: 800, letterSpacing: 1.6, textTransform: "uppercase", color: "#cbd5e1" }}>
                    Live Anti-Cheating Control Center
                  </span>
                </div>
                <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6 }}>
                  Real-time browser telemetry, proctor heartbeat status, and integrity scoring are active during this interview.
                </div>
              </div>
              <div style={{
                minWidth: 130,
                padding: "12px 14px",
                borderRadius: 18,
                background: tone.glow,
                border: `1px solid ${tone.color}40`,
                textAlign: "center",
              }}>
                <div style={{ fontSize: 11, color: "#cbd5e1", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>Integrity Score</div>
                <div style={{ fontSize: 28, fontWeight: 900, color: tone.color }}>{integrityScore}</div>
                <div style={{ fontSize: 11, color: "#e2e8f0" }}>{antiCheatSummary?.integrity_grade ?? tone.label}</div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12, marginBottom: 16 }}>
              <TelemetryStat
                icon={<Eye size={14} color="#38bdf8" />}
                label="Focus Alerts"
                value={String(sessionStatus?.tab_switch_count ?? antiCheatSummary?.tab_switch_count ?? 0)}
                tone="#38bdf8"
              />
              <TelemetryStat
                icon={<Activity size={14} color="#fbbf24" />}
                label="Warnings"
                value={String(antiCheatSummary?.warning_events ?? 0)}
                tone="#fbbf24"
              />
              <TelemetryStat
                icon={<AlertTriangle size={14} color="#f87171" />}
                label="Criticals"
                value={String(antiCheatSummary?.critical_events ?? 0)}
                tone="#f87171"
              />
              <TelemetryStat
                icon={<Bot size={14} color="#c084fc" />}
                label="AI Violations"
                value={String(sessionStatus?.ai_violations_count ?? antiCheatSummary?.ai_violations_count ?? 0)}
                tone="#c084fc"
              />
              <TelemetryStat
                icon={proctorHealth?.proctor_alive ? <ShieldCheck size={14} color="#4ade80" /> : <ShieldAlert size={14} color="#fbbf24" />}
                label="Proctor"
                value={proctorHealth?.proctor_alive ? "Live" : (session?.interview_mode === "enterprise" ? "Waiting" : "Optional")}
                tone={proctorHealth?.proctor_alive ? "#4ade80" : "#fbbf24"}
              />
              <TelemetryStat
                icon={<Zap size={14} color="#e2e8f0" />}
                label="Heartbeats"
                value={String(proctorHealth?.heartbeat_count ?? antiCheatSummary?.proctor_heartbeat_count ?? 0)}
                tone="#e2e8f0"
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div style={{
                padding: "14px 16px",
                borderRadius: 16,
                border: "1px solid rgba(148,163,184,0.16)",
                background: "rgba(7,15,30,0.68)",
              }}>
                <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>Decision Signals</div>
                <div style={{ display: "grid", gap: 8 }}>
                  <SignalRow label="Suspicious activity flag" value={suspiciousState ? "Raised" : "Clear"} color={suspiciousState ? "#fbbf24" : "#4ade80"} />
                  <SignalRow label="Browser alerts captured" value={String(antiCheatSummary?.browser_alerts ?? antiCheatSummary?.total_events ?? localEventFeed.length)} color="#38bdf8" />
                  <SignalRow label="Timer remaining" value={remainingMinutes != null ? `${remainingMinutes} min` : "Tracking"} color="#e2e8f0" />
                  <SignalRow label="Recent backend event" value={antiCheatSummary?.recent_event_type ? formatAntiCheatEvent(antiCheatSummary.recent_event_type) : "No backend alert yet"} color="#cbd5e1" />
                </div>
              </div>

              <div style={{
                padding: "14px 16px",
                borderRadius: 16,
                border: "1px solid rgba(148,163,184,0.16)",
                background: "rgba(7,15,30,0.68)",
              }}>
                <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>Response Guidance</div>
                <div style={{ display: "grid", gap: 8, fontSize: 13, color: "#cbd5e1", lineHeight: 1.6 }}>
                  <div>Keep this window focused and avoid opening browser tools, print dialogs, or copy/paste actions.</div>
                  <div>{session?.interview_mode === "enterprise" ? "Enterprise mode expects steady proctor heartbeat continuity." : "Practice mode still records integrity signals for the final report."}</div>
                  <div>{proctorHealth?.last_heartbeat_gap_seconds != null ? `Latest proctor heartbeat gap: ${proctorHealth.last_heartbeat_gap_seconds}s.` : "Waiting for the next telemetry refresh."}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="spatial-panel" style={{
            padding: "18px 18px 16px",
            borderRadius: 22,
            border: "1px solid rgba(167,139,250,0.18)",
            background: "linear-gradient(160deg, rgba(20,12,37,0.82), rgba(10,18,38,0.76))",
            boxShadow: "0 24px 70px rgba(2,6,23,0.36)",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 1.4, textTransform: "uppercase", color: "#e2e8f0" }}>Event Feed</div>
                <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>Newest backend and browser-side signals surface here live.</div>
              </div>
              <span style={{
                padding: "5px 9px",
                borderRadius: 999,
                fontSize: 10,
                fontWeight: 800,
                letterSpacing: 1,
                color: tone.color,
                background: tone.glow,
                border: `1px solid ${tone.color}40`,
              }}>
                {antiCheatSummary?.risk_level?.toUpperCase() ?? tone.label.toUpperCase()}
              </span>
            </div>

            <div style={{ display: "grid", gap: 10, marginBottom: 14 }}>
              {recentEvents.length > 0 ? recentEvents.map((event, index) => (
                <EventFeedRow
                  key={`${event.type}-${event.timestamp ?? index}`}
                  title={formatAntiCheatEvent(event.type)}
                  details={event.details || "Signal captured by the integrity engine."}
                  severity={event.severity}
                  timestamp={event.timestamp}
                />
              )) : (
                <div style={{
                  padding: "14px 16px",
                  borderRadius: 14,
                  background: "rgba(15,23,42,0.55)",
                  border: "1px solid rgba(148,163,184,0.12)",
                  color: "#94a3b8",
                  fontSize: 13,
                  lineHeight: 1.6,
                }}>
                  Backend anti-cheat telemetry is active. Browser and proctor signals will appear here as soon as activity is recorded.
                </div>
              )}
            </div>

            {localEventFeed.length > 0 && (
              <div style={{
                paddingTop: 12,
                borderTop: "1px solid rgba(148,163,184,0.14)",
              }}>
                <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>
                  Local Browser Watchers
                </div>
                <div style={{ display: "grid", gap: 8 }}>
                  {localEventFeed.slice(0, 4).map((event) => (
                    <div
                      key={`${event.type}-${event.at}`}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 12,
                        padding: "10px 12px",
                        borderRadius: 12,
                        background: "rgba(15,23,42,0.45)",
                        border: "1px solid rgba(56,189,248,0.12)",
                      }}
                    >
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: "#e2e8f0", marginBottom: 2 }}>{formatAntiCheatEvent(event.type)}</div>
                        <div style={{ fontSize: 11, color: "#94a3b8", lineHeight: 1.5 }}>{event.details}</div>
                      </div>
                      <div style={{ fontSize: 11, color: "#64748b", whiteSpace: "nowrap" }}>
                        {new Date(event.at).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
          <div style={{ fontSize: 18, fontWeight: 800, color: "#15304b", marginBottom: 2 }}>
            Aria
          </div>
          <div style={{ fontSize: 11, color: "#5d728a", marginBottom: 16, letterSpacing: 0.5 }}>
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
            background: "rgba(255,255,255,0.84)", backdropFilter: "blur(12px)",
            border: "1px solid rgba(148,163,184,0.18)", borderRadius: 20,
            padding: "28px 32px", textAlign: "center",
            boxShadow: `0 18px 40px rgba(37,99,235,0.08)`,
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700, color: "#5d728a",
              textTransform: "uppercase", letterSpacing: 2, marginBottom: 12,
            }}>
              Question {turnNumber}
            </div>
            <p style={{
              fontSize: 20, fontWeight: 600, lineHeight: 1.6, color: "#15304b",
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
            background: "rgba(255,247,237,0.96)", border: "1px solid rgba(249,115,22,0.18)",
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
            {report.interview_mode === "enterprise" ? "Enterprise Assessment" : "Practice Session"} • {report.answered_turns}/{report.total_questions} questions answered
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
            <StatBox label="Mode" value={report.interview_mode === "enterprise" ? "Enterprise" : "Practice"} />
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

function TelemetryStat({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div style={{
      padding: "12px 14px",
      borderRadius: 16,
      border: "1px solid rgba(148,163,184,0.14)",
      background: "rgba(7,15,30,0.68)",
      minHeight: 88,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: `${tone}18`,
          border: `1px solid ${tone}30`,
        }}>
          {icon}
        </div>
        <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1.1 }}>{label}</span>
      </div>
      <div style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc" }}>{value}</div>
    </div>
  );
}

function SignalRow({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
      <span style={{ color: "#94a3b8", fontSize: 12 }}>{label}</span>
      <span style={{ color, fontWeight: 700, fontSize: 12, textAlign: "right" }}>{value}</span>
    </div>
  );
}

function EventFeedRow({
  title,
  details,
  severity,
  timestamp,
}: {
  title: string;
  details: string;
  severity: string;
  timestamp: string | null;
}) {
  const tone = severity === "critical"
    ? { color: "#f87171", bg: "rgba(248,113,113,0.1)", border: "rgba(248,113,113,0.2)" }
    : severity === "warning"
      ? { color: "#fbbf24", bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.18)" }
      : { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.18)" };

  return (
    <div style={{
      padding: "12px 14px",
      borderRadius: 14,
      background: tone.bg,
      border: `1px solid ${tone.border}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: tone.color, boxShadow: `0 0 16px ${tone.color}70` }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>{title}</span>
        </div>
        <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: 1, color: tone.color, textTransform: "uppercase" }}>{severity}</span>
      </div>
      <div style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.6, marginBottom: 4 }}>{details}</div>
      <div style={{ fontSize: 11, color: "#64748b" }}>
        {timestamp ? new Date(timestamp).toLocaleTimeString() : "Just now"}
      </div>
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
  background: "linear-gradient(180deg, rgba(18,18,42,0.84), rgba(10,10,24,0.92))",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 24,
  padding: 28,
  backdropFilter: "blur(18px)",
  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.08), 0 24px 60px rgba(3,2,20,0.42)",
};

const labelStyle: CSSProperties = {
  display: "block", fontSize: 12, fontWeight: 600, color: "#94a3b8",
  marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5,
};

const inputStyle: CSSProperties = {
  width: "100%", padding: "12px 16px", borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.1)", background: "rgba(9,9,24,0.72)",
  color: "#f1f5f9", fontSize: 14, outline: "none", transition: "border-color 0.3s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
};

const primaryBtnStyle: CSSProperties = {
  padding: "14px 32px", borderRadius: 12, border: "none", fontWeight: 700, fontSize: 14,
  color: "#fff", cursor: "pointer",
  background: "linear-gradient(135deg, #7c3aed, #f43f5e)",
  boxShadow: "0 10px 30px rgba(124,58,237,0.28)",
  transition: "all 0.3s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
};

const backBtnStyle: CSSProperties = {
  background: "none", border: "none", color: "#64748b", cursor: "pointer",
  fontSize: 13, fontWeight: 500, marginBottom: 20, padding: 0,
  transition: "color 0.2s ease",
  fontFamily: "var(--font-source-sans), sans-serif",
};
