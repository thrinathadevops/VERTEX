"use client";

import { useState, useEffect, useRef } from "react";
import { Mic, Video, ShieldCheck, Activity, BrainCircuit, XCircle, ChevronRight, Pause, Play } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function MockAIInterview() {
  const router = useRouter();
  const [phase, setPhase] = useState("AI Introduction");
  const [timer, setTimer] = useState(2700); // 45 minutes limit
  
  // Real camera feed
  const cameraRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Start webcam for the mock
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        if (cameraRef.current) cameraRef.current.srcObject = stream;
      })
      .catch(err => console.log("Camera access denied for mock demo."));

    // Timer countdown
    const int = setInterval(() => setTimer(prev => prev > 0 ? prev - 1 : 0), 1000);
    return () => clearInterval(int);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="relative w-full h-[85vh] rounded-3xl border border-slate-800 bg-[#0B1120] text-slate-300 flex flex-col font-sans overflow-hidden shadow-2xl mt-4">
      
      {/* ── TOP NAV ──────────────────────────────────────────────────────── */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between px-6 shrink-0 z-10 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <BrainCircuit className="w-6 h-6 text-cyan-400" />
          <h1 className="font-bold tracking-widest uppercase text-sm text-slate-200">
            VAREX <span className="text-slate-500 mx-2">|</span> AI Assessment Engine
          </h1>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-1.5 rounded-full">
            <ShieldCheck className="w-4 h-4" /> Proctoring Active
          </div>
          <div className="text-xl font-mono font-bold text-white tracking-wider flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-400" /> {formatTime(timer)}
          </div>
          <button onClick={() => router.push("/hire")} className="text-slate-400 hover:text-white transition-colors">
            <XCircle className="w-6 h-6" />
          </button>
        </div>
      </header>

      {/* ── MAIN INTERFACE ──────────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT PANEL: Progress & Camera */}
        <div className="w-80 border-r border-slate-800 bg-slate-900/30 flex flex-col shrink-0">
          
          {/* Phase Tracker */}
          <div className="flex-1 p-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-6">Assessment Phases</h3>
            <ul className="space-y-6 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px before:h-full before:w-0.5 before:bg-slate-800">
              {["AI Introduction", "Ice-Breaker (Resume)", "Technical Deep Dive", "System Design", "Behavioral Evaluation"].map((p, i) => (
                <li key={i} className="relative flex items-center gap-4">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 border-2
                    ${i === 1 ? "bg-cyan-500 border-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" 
                      : i < 1 ? "bg-slate-700 border-slate-700" : "bg-slate-900 border-slate-700"}
                  `}>
                    {i < 1 && <CheckCircle className="w-3 h-3 text-white" />}
                    {i === 1 && <div className="w-2 h-2 rounded-full bg-white animate-pulse" />}
                  </div>
                  <span className={`text-sm ${i === 1 ? "text-cyan-400 font-bold" : i < 1 ? "text-slate-400" : "text-slate-500"}`}>
                    {p}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Picture in Picture (Camera) */}
          <div className="h-64 border-t border-slate-800 bg-black relative p-2">
             <div className="absolute top-4 left-4 z-10 bg-black/60 backdrop-blur-md border border-slate-700 px-2 py-1 rounded text-[10px] font-mono text-white flex items-center gap-2">
               <Video className="w-3 h-3 text-red-500" /> RECORDING
             </div>
             <video ref={cameraRef} autoPlay playsInline muted className="w-full h-full object-cover rounded-lg border border-slate-800 transform -scale-x-100" />
          </div>
        </div>

        {/* RIGHT PANEL: AI Voice Engine */}
        <div className="flex-1 flex flex-col bg-[#0B1120] relative">
          
          {/* AI Orb visualization */}
          <div className="flex-1 flex items-center justify-center relative">
            <div className="absolute inset-0 bg-gradient-to-b from-cyan-900/10 to-transparent" />
            
            {/* The Orb */}
            <div className="relative flex items-center justify-center w-64 h-64">
              <div className="absolute inset-0 rounded-full bg-cyan-500/10 animate-ping" style={{ animationDuration: '3s' }} />
              <div className="absolute inset-4 rounded-full bg-cyan-400/20 blur-xl animate-pulse" />
              <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-cyan-600 to-sky-400 shadow-[0_0_50px_rgba(34,211,238,0.4)] flex items-center justify-center z-10 border border-cyan-300/30">
                <Mic className="w-10 h-10 text-white drop-shadow-md animate-pulse" />
              </div>
            </div>
          </div>

          {/* Transcript / Dialog Box */}
          <div className="h-80 border-t border-slate-800 bg-slate-900/50 p-8 flex flex-col justify-end relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-12 bg-gradient-to-b from-slate-900/50 to-transparent" />
            
            <div className="space-y-6 mt-auto">
              {/* Previous Message (Faded) */}
              <div className="flex gap-4 opacity-40">
                <div className="w-8 h-8 rounded-full bg-cyan-900 flex items-center justify-center shrink-0">
                  <BrainCircuit className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="bg-slate-800 rounded-2xl rounded-tl-sm px-5 py-3 text-sm max-w-2xl">
                  Hello, I am VAREX, your autonomous technical evaluator. Are you ready to begin?
                </div>
              </div>

              {/* User Response */}
              <div className="flex gap-4 flex-row-reverse">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-white">YOU</span>
                </div>
                <div className="bg-indigo-500/20 border border-indigo-500/30 text-indigo-100 rounded-2xl rounded-tr-sm px-5 py-3 text-sm max-w-2xl">
                  Yes, I'm ready. Let's start.
                </div>
              </div>

              {/* Current AI Message */}
              <div className="flex gap-4 items-end">
                <div className="w-10 h-10 rounded-full bg-cyan-500 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(6,182,212,0.4)] relative">
                  <div className="absolute -inset-1 rounded-full border border-cyan-400/50 animate-ping" />
                  <BrainCircuit className="w-5 h-5 text-white" />
                </div>
                <div className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-50 rounded-2xl rounded-tl-sm px-6 py-4 max-w-3xl shadow-lg">
                  <p className="text-base leading-relaxed">
                    Excellent. Let's move to the Ice-Breaker. I see on your resume you spent 3 years at TechCorp migrating their monolith to a microservices architecture using Kubernetes. 
                    <br/><br/>
                    Can you walk me through the specific networking hurdles you faced configuring the ingress controllers during that migration?
                  </p>
                </div>
              </div>
            </div>

            {/* Speaking Controls */}
            <div className="absolute bottom-6 right-8 flex items-center gap-4">
              <div className="text-xs text-slate-400 uppercase tracking-widest font-bold flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening...
              </div>
              <button className="w-12 h-12 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-full flex items-center justify-center transition-colors">
                <Pause className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Re-usable check icon
function CheckCircle(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
      <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
  );
}
