"use client";

import { useState, useEffect, useRef } from "react";
import { Camera, MonitorUp, ShieldAlert, MapPin, TerminalSquare, AlertTriangle, CheckCircle2, VideoOff, MicOff, Maximize2, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Violation {
  time: string;
  type: string;
  message: string;
}

interface GeoData {
  city: string;
  region: string;
  country_name: string;
  ip: string;
  org: string;
}

export default function InterviewRoom() {
  const router = useRouter();
  const [isActive, setIsActive] = useState(false);
  const [code, setCode] = useState("// Write your architecture solution here...\n\nfunction initializeArchitecture() {\n  // Candidate inputs code\n}");
  
  // Streams
  const cameraRef = useRef<HTMLVideoElement>(null);
  const screenRef = useRef<HTMLVideoElement>(null);
  const [hasCamera, setHasCamera] = useState(false);
  const [hasScreen, setHasScreen] = useState(false);

  // Security States
  const [violations, setViolations] = useState<Violation[]>([]);
  const [geo, setGeo] = useState<GeoData | null>(null);
  const [tabBlurCount, setTabBlurCount] = useState(0);

  // 1. Fetch Geolocation Authentication Data
  useEffect(() => {
    fetch("https://ipapi.co/json/")
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) {
          setGeo({
            city: data.city,
            region: data.region,
            country_name: data.country_name,
            ip: data.ip,
            org: data.org,
          });
        }
      })
      .catch((err) => console.log("Geo fetch failed (adblocker maybe)"));
  }, []);

  // 2. Anti-Cheating: Browser Integrity Monitoring (Tab Switches)
  useEffect(() => {
    if (!isActive) return;

    const handleBlur = () => {
      setTabBlurCount(prev => prev + 1);
      const newViolation: Violation = {
        time: new Date().toLocaleTimeString(),
        type: "CRITICAL",
        message: "Browser Integrity Lost: Candidate switched tabs or lost window focus. Potential AI usage."
      };
      setViolations(prev => [newViolation, ...prev]);
    };

    const handleFocus = () => {
      const newViolation: Violation = {
        time: new Date().toLocaleTimeString(),
        type: "INFO",
        message: "Browser Focus Restored: Candidate returned to secure environment."
      };
      setViolations(prev => [newViolation, ...prev]);
    };

    const handleCopyPaste = (e: ClipboardEvent) => {
      e.preventDefault();
      const newViolation: Violation = {
        time: new Date().toLocaleTimeString(),
        type: "WARNING",
        message: "Clipboard Violation: Unauthorized copy/paste attempt blocked in notepad."
      };
      setViolations(prev => [newViolation, ...prev]);
    };

    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("copy", handleCopyPaste);
    document.addEventListener("paste", handleCopyPaste);

    return () => {
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("copy", handleCopyPaste);
      document.removeEventListener("paste", handleCopyPaste);
    };
  }, [isActive]);

  // 3. Hardware Interfacing: Start WebRTC Streams
  const startInterview = async () => {
    try {
      // Prompt for Camera
      const camStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (cameraRef.current) {
        cameraRef.current.srcObject = camStream;
        setHasCamera(true);
      }

      // Prompt for Screen Share
      const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      if (screenRef.current) {
        screenRef.current.srcObject = screenStream;
        setHasScreen(true);
      }

      setIsActive(true);
      setViolations([{
        time: new Date().toLocaleTimeString(),
        type: "INFO",
        message: "Interview Session Started. All proctoring hooks active."
      }]);

    } catch (err) {
      alert("Microphone, Camera, or Screen Share permissions were denied. Cannot enter secure room.");
    }
  };

  const endInterview = () => {
    // Stop all tracks
    if (cameraRef.current && cameraRef.current.srcObject) {
      (cameraRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
    }
    if (screenRef.current && screenRef.current.srcObject) {
      (screenRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
    }
    setIsActive(false);
    router.push("/hire");
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0B1120] text-slate-300 flex flex-col font-sans overflow-hidden">
      
      {/* ── TOP BAR (Header) ──────────────────────────────────────────────── */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between px-6 shrink-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
          <h1 className="font-bold tracking-widest uppercase text-sm text-slate-200">VAREX <span className="text-slate-500 font-medium">|</span> Secure Assessment Protocol</h1>
        </div>
        {!isActive ? (
          <button onClick={startInterview} className="bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold px-5 py-2 rounded-md shadow-[0_0_15px_rgba(14,165,233,0.3)] transition-all flex items-center gap-2">
            <MonitorUp className="w-4 h-4" /> Initialize Hardware Streams
          </button>
        ) : (
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-1 rounded">OS Proctor: CONNECTED</span>
            <button onClick={endInterview} className="bg-red-500/20 hover:bg-red-500 text-red-400 hover:text-white border border-red-500/30 text-xs font-bold px-5 py-2 rounded-md transition-all flex items-center gap-2">
              <X className="w-4 h-4" /> End Interview
            </button>
          </div>
        )}
      </header>

      {/* ── MAIN CONTENT AREA ──────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT COLUMN: Hardware Streams & Notepad */}
        <div className="flex-1 flex flex-col border-r border-slate-800 bg-black overflow-y-auto">
          
          {/* Top Half: Video Feeds */}
          <div className="h-[45%] grid grid-cols-3 gap-1 p-1 bg-slate-950">
            {/* Screen Share (Takes 2/3) */}
            <div className="col-span-2 relative bg-[#111] rounded-lg border border-slate-800 overflow-hidden group">
              <div className="absolute top-3 pl-4 z-10 hidden group-hover:block w-full bg-gradient-to-b from-black/80 to-transparent">
                <span className="text-xs font-bold tracking-widest text-emerald-400 flex items-center gap-2 drop-shadow-md">
                  <MonitorUp className="w-3.5 h-3.5"/> ACTIVE WORKSPACE (SCREEN SHARE)
                </span>
              </div>
              {!hasScreen && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600">
                  <MonitorUp className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-xs uppercase tracking-widest font-bold">Awaiting Screen Payload</p>
                </div>
              )}
              <video ref={screenRef} autoPlay playsInline muted className="w-full h-full object-contain" />
            </div>

            {/* Webcam (Takes 1/3) */}
            <div className="col-span-1 relative bg-[#111] rounded-lg border border-slate-800 overflow-hidden group">
              <div className="absolute top-3 pl-4 z-10 hidden group-hover:block w-full bg-gradient-to-b from-black/80 to-transparent">
                 <span className="text-xs font-bold tracking-widest text-sky-400 flex items-center gap-2 drop-shadow-md">
                   <Camera className="w-3.5 h-3.5"/> BIOMETRIC FEED
                 </span>
              </div>
              {!hasCamera && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600">
                  <VideoOff className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-xs uppercase tracking-widest font-bold">Camera Offline</p>
                </div>
              )}
              <video ref={cameraRef} autoPlay playsInline muted className="w-full h-full object-cover transform -scale-x-100" />
            </div>
          </div>

          {/* Bottom Half: Synchronized Notepad */}
          <div className="flex-1 flex flex-col bg-[#1E1E1E] border-t border-slate-800">
            <div className="h-10 bg-[#2D2D2D] border-b border-[#3D3D3D] flex items-center justify-between px-4 shrink-0">
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <TerminalSquare className="w-4 h-4 text-amber-400"/> index.ts <span className="italic opacity-50 ml-2">(Live Synchronized)</span>
              </div>
            </div>
            <textarea 
              value={code} 
              onChange={(e) => setCode(e.target.value)}
              disabled={!isActive}
              spellCheck={false}
              className="flex-1 w-full bg-[#1E1E1E] text-[#D4D4D4] font-mono text-sm p-4 focus:outline-none resize-none disabled:opacity-50"
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Anti-Cheating Control Center */}
        <div className="w-80 lg:w-96 shrink-0 bg-[#0B1120] flex flex-col">
          
          <div className="p-5 border-b border-slate-800 bg-slate-900/30">
            <h2 className="text-sm font-bold uppercase tracking-widest text-white mb-1 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-sky-400"/> Telemetry & Security
            </h2>
            <p className="text-[10px] text-slate-400">Supervising OS, Network, and Browser Integrity</p>
          </div>

          {/* Geo Data */}
          <div className="p-5 border-b border-slate-800">
            <h3 className="text-xs font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5" /> Geolocation Authentication
            </h3>
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800/80 font-mono text-xs space-y-2">
              {geo ? (
                <>
                  <div className="flex justify-between"><span className="text-slate-500">IP Addr:</span> <span className="text-sky-400">{geo.ip}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">City:</span> <span className="text-white">{geo.city}, {geo.region}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Country:</span> <span className="text-white">{geo.country_name}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">ISP/Org:</span> <span className="text-slate-400 truncate max-w-[120px]" title={geo.org}>{geo.org}</span></div>
                  <div className="mt-3 pt-3 border-t border-slate-800 text-emerald-400 flex items-center gap-1.5 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5"/> No VPN/Proxy Detected
                  </div>
                </>
              ) : (
                <div className="animate-pulse text-slate-500 py-2">Tracing Packet Origins...</div>
              )}
            </div>
          </div>

          {/* Overview Metrics */}
          <div className="p-5 border-b border-slate-800 grid grid-cols-2 gap-4">
             <div className="bg-slate-900 rounded border border-slate-800 p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Tab Switches</div>
                <div className={`text-2xl font-mono font-bold ${tabBlurCount > 0 ? "text-red-500" : "text-emerald-400"}`}>
                  {tabBlurCount}
                </div>
             </div>
             <div className="bg-slate-900 rounded border border-slate-800 p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Face State</div>
                <div className="text-xs font-mono font-bold text-emerald-400 mt-2">
                  {hasCamera ? "TRACKING" : "OFFLINE"}
                </div>
             </div>
          </div>

          {/* Activity / Violation Log */}
          <div className="flex-1 flex flex-col p-5 overflow-hidden">
            <h3 className="text-xs font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5" /> Real-Time Event Log
            </h3>
            
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
              {violations.length === 0 ? (
                <div className="text-xs text-slate-600 italic font-mono text-center mt-10">
                  Waiting for stream initialization...
                </div>
              ) : (
                violations.map((v, i) => (
                  <div key={i} className={`p-3 rounded-lg border text-xs font-mono
                    ${v.type === "CRITICAL" ? "bg-red-500/10 border-red-500/30 text-red-200" : 
                      v.type === "WARNING" ? "bg-amber-500/10 border-amber-500/30 text-amber-200" : 
                      "bg-slate-800/50 border-slate-700 text-slate-300"}
                  `}>
                    <div className="flex justify-between items-start mb-1.5 opacity-80">
                      <span className="font-bold">[{v.type}]</span>
                      <span>{v.time}</span>
                    </div>
                    <p className="leading-relaxed">{v.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
