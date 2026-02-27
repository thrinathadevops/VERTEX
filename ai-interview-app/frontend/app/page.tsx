"use client";

import { FormEvent, useMemo, useState } from "react";

type SessionPayload = {
  id: string;
  status: string;
  first_question: string;
};

type AnswerPayload = {
  score: number;
  feedback: string;
  next_question: string | null;
  status: string;
};

type ReportPayload = {
  session_id: string;
  status: string;
  answered_turns: number;
  average_score: number;
  recommendation: string;
  generated_at: string;
};

export default function HomePage() {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [targetRole, setTargetRole] = useState("DevOps Engineer");
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [lastAnswer, setLastAnswer] = useState<AnswerPayload | null>(null);
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmitAnswer = useMemo(() => !!session && !!currentQuestion && answer.trim().length >= 5, [session, currentQuestion, answer]);

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
        }),
      });
      if (!res.ok) {
        throw new Error("Failed to start interview session.");
      }
      const data: SessionPayload = await res.json();
      setSession(data);
      setCurrentQuestion(data.first_question);
      setAnswer("");
      setLastAnswer(null);
      setReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start interview session.");
    } finally {
      setLoading(false);
    }
  }

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
      if (!res.ok) {
        throw new Error("Failed to submit answer.");
      }
      const data: AnswerPayload = await res.json();
      setLastAnswer(data);
      setAnswer("");
      setCurrentQuestion(data.next_question ?? "");
      if (data.status === "completed") {
        await fetchReport(session.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answer.");
    } finally {
      setLoading(false);
    }
  }

  async function fetchReport(sessionId: string) {
    const res = await fetch(`/api/v1/interview/session/${sessionId}/report`);
    if (!res.ok) {
      throw new Error("Failed to load interview report.");
    }
    const data: ReportPayload = await res.json();
    setReport(data);
  }

  return (
    <main>
      <h1>VAREX AI Interview App</h1>
      <p className="muted">Standalone application with dedicated app/web/db infrastructure.</p>

      {!session && (
        <form className="panel" onSubmit={startSession}>
          <h2>Start Interview</h2>
          <label>Candidate Name</label>
          <input value={candidateName} onChange={(e) => setCandidateName(e.target.value)} required />
          <label>Candidate Email</label>
          <input type="email" value={candidateEmail} onChange={(e) => setCandidateEmail(e.target.value)} required />
          <label>Target Role</label>
          <input value={targetRole} onChange={(e) => setTargetRole(e.target.value)} required />
          <button disabled={loading}>{loading ? "Starting..." : "Create Session"}</button>
        </form>
      )}

      {session && (
        <section className="panel">
          <h2>Session: {session.id}</h2>
          {currentQuestion ? (
            <>
              <p><strong>Question:</strong> {currentQuestion}</p>
              <textarea rows={6} value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Write your answer here..." />
              <button disabled={!canSubmitAnswer || loading} onClick={submitCurrentAnswer}>
                {loading ? "Submitting..." : "Submit Answer"}
              </button>
            </>
          ) : (
            <p>Interview completed. Report generated below.</p>
          )}
        </section>
      )}

      {lastAnswer && (
        <section className="panel">
          <h3>Last Evaluation</h3>
          <p><strong>Score:</strong> {lastAnswer.score}/10</p>
          <p><strong>Feedback:</strong> {lastAnswer.feedback}</p>
          <p><strong>Status:</strong> {lastAnswer.status}</p>
        </section>
      )}

      {report && (
        <section className="panel">
          <h3>Final Report</h3>
          <p><strong>Answered Turns:</strong> {report.answered_turns}</p>
          <p><strong>Average Score:</strong> {report.average_score}</p>
          <p><strong>Recommendation:</strong> {report.recommendation}</p>
          <p className="muted">Generated: {new Date(report.generated_at).toLocaleString()}</p>
        </section>
      )}

      {error && <div className="error">{error}</div>}
    </main>
  );
}
