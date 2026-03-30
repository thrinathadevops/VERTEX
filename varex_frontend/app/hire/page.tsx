"use client";

import Link from "next/link";
import { Shield, BrainCircuit, UserCheck, Video, FileText, MapPin, Eye, TerminalSquare, AlertTriangle } from "lucide-react";
import AnimateIn from "@/components/AnimateIn";

export default function HirePage() {
  return (
    <div className="space-y-16 pb-20">
      
      {/* ── HERO ──────────────────────────────────────────────────────── */}
      <header className="text-center pt-8">
        <span className="inline-block rounded-full bg-cyan-500/10 border border-cyan-500/20 px-4 py-1.5 text-xs font-semibold tracking-wide text-cyan-400 mb-6 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
          VAREX TALENT AUTHENTICATION ENGINE
        </span>
        <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight leading-tight">
          Next-Generation Technical <br className="hidden sm:block" /> Screening & Authentication.
        </h1>
        <p className="text-slate-300 max-w-2xl mx-auto text-sm md:text-base mb-8 leading-relaxed">
          We have engineered the industry's most rigorous, tamper-proof hiring pipeline. From autonomous mock screens to live, biometrically-audited client video conferences.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/contact?service=ai_hiring"
            className="w-full sm:w-auto rounded-xl bg-cyan-500 hover:bg-cyan-400 px-8 py-3.5 text-sm font-bold text-white shadow-[0_0_30px_rgba(6,182,212,0.3)] transition-all">
            Deploy Enterprise Pipeline
          </Link>
          <Link href="/ai-interview"
            className="w-full sm:w-auto rounded-xl border border-slate-700 bg-slate-900/50 hover:bg-slate-800 hover:border-cyan-500 px-8 py-3.5 text-sm font-bold text-slate-300 hover:text-white transition-all">
            Take a Mock Interview
          </Link>
        </div>
      </header>

      {/* ── TWO PILLARS ──────────────────────────────────────────────────────── */}
      <section className="grid md:grid-cols-2 gap-8 lg:gap-12 max-w-6xl mx-auto">
        
        {/* Pillar 1: Mock Interviews */}
        <AnimateIn delay={0.1}>
          <div className="h-full rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-[#0B1120] p-8 lg:p-10 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-colors" />
            <div className="relative">
              <div className="w-14 h-14 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mb-6">
                <BrainCircuit className="w-7 h-7 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">Method 1: Mock Interviews</h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-8">
                Designed exclusively for candidates looking to sharpen their technical acumen. Run unlimited practice interviews against our autonomous AI engine to simulate high-pressure environment questions, from System Design to LeetCode-style algorithms.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start gap-4 text-sm text-slate-300">
                  <div className="mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Interactive conversational AI architecture.</span>
                </li>
                <li className="flex items-start gap-4 text-sm text-slate-300">
                  <div className="mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Real-time technical feedback and grading rubrics.</span>
                </li>
              </ul>
            </div>
          </div>
        </AnimateIn>

        {/* Pillar 2: Enterprise Interviews */}
        <AnimateIn delay={0.2}>
          <div className="h-full rounded-3xl border border-sky-900/50 bg-gradient-to-b from-sky-950/20 to-[#0B1120] p-8 lg:p-10 shadow-[0_0_50px_rgba(14,165,233,0.05)] relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl group-hover:bg-sky-500/15 transition-colors" />
            <div className="relative">
              <div className="w-14 h-14 bg-sky-500/20 border border-sky-500/30 rounded-2xl flex items-center justify-center mb-6 shadow-[0_0_20px_rgba(14,165,233,0.3)]">
                <Shield className="w-7 h-7 text-sky-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">Method 2: Enterprise Pipeline</h2>
              <p className="text-slate-300 text-sm leading-relaxed mb-8 font-medium">
                The ultimate B2B technical screening funnel. We do not just find engineers; we relentlessly authenticate their logic and identity before you even look at their resume.
              </p>
              
              <div className="space-y-5 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-sky-500/20 before:to-transparent">
                
                {/* Step 1 */}
                <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full border border-sky-500 bg-slate-900 text-sky-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                    <div className="w-2 h-2 rounded-full bg-sky-400" />
                  </div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2rem)] p-4 rounded-xl border border-slate-800 bg-slate-900/80">
                    <h3 className="font-bold text-sky-300 text-sm mb-1 flex items-center gap-2"><FileText className="w-3 h-3"/> JD vs. Resume Scan</h3>
                    <p className="text-xs text-slate-400">Deep-scanning incoming resumes against your exact Job Description to instantly filter unqualified applicants.</p>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full border border-sky-500 bg-slate-900 text-sky-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                    <div className="w-2 h-2 rounded-full bg-sky-400" />
                  </div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2rem)] p-4 rounded-xl border border-slate-800 bg-slate-900/80">
                    <h3 className="font-bold text-sky-300 text-sm mb-1 flex items-center gap-2"><BrainCircuit className="w-3 h-3"/> Autonomous AI Screen</h3>
                    <p className="text-xs text-slate-400">Candidates undergo a rigorous, conversational AI interview to validate baseline logic before taking up your time.</p>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full border border-sky-500 bg-slate-900 text-amber-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                    <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  </div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2rem)] p-4 rounded-xl border border-sky-900/50 bg-[#0B1120] shadow-[0_0_15px_rgba(14,165,233,0.1)]">
                    <h3 className="font-bold text-amber-400 text-sm mb-1 flex items-center gap-2"><Video className="w-3 h-3"/> Secure Client Slotting</h3>
                    <p className="text-xs text-slate-300">Once cleared, the system dynamically generates a secure Video Conference link synchronized to the Client's availability.</p>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </AnimateIn>

      </section>

      {/* ── LIVE INTERVIEW ROOM EXPLAINER ────────────────────────────────────────── */}
      <AnimateIn delay={0.3}>
        <section className="max-w-6xl mx-auto mt-20">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold mb-4">The Live Anti-Cheating Control Center</h2>
            <p className="text-slate-400 text-sm max-w-2xl mx-auto">
              When the client enters the Video Conference via the generated link, they are not just entering a Zoom call. They are stepping into a heavily instrumented, biometrically-monitored technical assessment suite.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Feature 1: Screen Share */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors">
              <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                <Video className="w-5 h-5 text-emerald-400" />
              </div>
              <h3 className="font-bold text-white mb-2 text-sm">Mandatory Screen Share</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Candidates are securely sandboxed. They must share their entire screen before entering the interview, giving clients uncompromised visibility into their active workspace.
              </p>
            </div>

            {/* Feature 2: Code Notepad */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors">
              <div className="w-12 h-12 bg-sky-500/10 rounded-xl flex items-center justify-center mb-4 border border-sky-500/20 shadow-[0_0_15px_rgba(14,165,233,0.1)]">
                <TerminalSquare className="w-5 h-5 text-sky-400" />
              </div>
              <h3 className="font-bold text-white mb-2 text-sm">Synchronized Code Notepad</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                A persistent, collaborative Notepad sits right in the call, allowing the client to request live architecture diagrams or code snippets instantly during the evaluation.
              </p>
            </div>

            {/* Feature 3: OS-Level Proctoring */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors">
              <div className="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center mb-4 border border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.1)]">
                <BrainCircuit className="w-5 h-5 text-amber-400" />
              </div>
              <h3 className="font-bold text-white mb-2 text-sm">OS-Level Proctoring Agent</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                We deploy a dedicated desktop agent that continuously scans running processes for known cheating software, AI injectors, and unauthorized network hooks during the screen.
              </p>
            </div>

            {/* Feature 4: Browser Integrity */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors">
              <div className="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center mb-4 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]">
                <Shield className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="font-bold text-white mb-2 text-sm">Browser Integrity Monitoring</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Candidates are locked into a strict environment. Our engine tracks and logs every single tab switch, window blur, and unauthorized copy/paste action with timestamped alerts.
              </p>
            </div>

            {/* Feature 5: Biometric Tracking */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-2xl" />
              <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center mb-4 border border-red-500/20 z-10 shadow-[0_0_15px_rgba(239,68,68,0.15)]">
                <Eye className="w-5 h-5 text-red-400" />
              </div>
              <h3 className="font-bold text-red-200 mb-2 text-sm z-10">Biometric Camera Tracking</h3>
              <p className="text-xs text-slate-400 leading-relaxed z-10">
                Continuous webcam monitoring ensures the primary candidate is present. The system automatically flags "face missing", "multiple faces detected", or sustained gaze deviation.
              </p>
            </div>

            {/* Feature 6: Geolocation Auth */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col items-center text-center hover:bg-slate-800/60 transition-colors">
              <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center mb-4 border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.1)]">
                <MapPin className="w-5 h-5 text-purple-400" />
              </div>
              <h3 className="font-bold text-white mb-2 text-sm">Live Geolocation Display</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                A persistent Client-Side Sidebar visualizes the Candidate's live geographical location via IP tracking to instantly flag VPN abuse or outsourced proxy engineering attempts.
              </p>
            </div>
            
          </div>
        </section>
      </AnimateIn>

    </div>
  );
}
