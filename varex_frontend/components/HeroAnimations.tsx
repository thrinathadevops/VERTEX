"use client";

import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Shield, Zap, Server, Lock } from "lucide-react";
import PlexusBackground from "./PlexusBackground";

// ─── Typewriter ────────────────────────────────────────────────────────────────
const PHRASES = [
  "DevSecOps Engineering.",
  "Cloud Infrastructure.",
  "Secure CI/CD Pipelines.",
  "Kubernetes Orchestration.",
  "Zero-Trust Architecture.",
];

function Typewriter() {
  const [phraseIdx, setPhraseIdx]   = useState(0);
  const [displayed, setDisplayed]   = useState("");
  const [deleting, setDeleting]     = useState(false);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (reduceMotion) { setDisplayed(PHRASES[0]); return; }
    const full = PHRASES[phraseIdx];
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && displayed.length < full.length) {
      timeout = setTimeout(() => setDisplayed(full.slice(0, displayed.length + 1)), 60);
    } else if (!deleting && displayed.length === full.length) {
      timeout = setTimeout(() => setDeleting(true), 2500); // 2.5s hold time
    } else if (deleting && displayed.length > 0) {
      timeout = setTimeout(() => setDisplayed(displayed.slice(0, -1)), 35);
    } else if (deleting && displayed.length === 0) {
      setDeleting(false);
      setPhraseIdx((i) => (i + 1) % PHRASES.length);
    }
    return () => clearTimeout(timeout);
  }, [displayed, deleting, phraseIdx, reduceMotion]);

  return (
    <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-cyan-300">
      {displayed}
      <motion.span
        animate={{ opacity: [1, 0, 1] }}
        transition={{ duration: 0.8, repeat: Infinity }}
        className="inline-block ml-[2px] w-[3px] h-[0.9em] bg-sky-400 translate-y-1"
      />
    </span>
  );
}

// ─── Glowing tech badge ───────────────────────────────────────────────────────
const TECH_BADGES = [
  { icon: <Shield className="w-3.5 h-3.5" />, label: "DevSecOps",  color: "from-sky-500/10 to-transparent",    border: "border-sky-500/20" },
  { icon: <Server className="w-3.5 h-3.5" />, label: "Kubernetes", color: "from-indigo-500/10 to-transparent", border: "border-indigo-500/20" },
  { icon: <Zap    className="w-3.5 h-3.5" />, label: "CI/CD",      color: "from-blue-500/10 to-transparent",   border: "border-blue-500/20" },
  { icon: <Lock   className="w-3.5 h-3.5" />, label: "Zero-Trust", color: "from-emerald-500/10 to-transparent", border: "border-emerald-500/20" },
];

// ─── Component exported for embedding in the hero ────────────────────────────
type HeroAnimationsProps = {
  start?: boolean;
};

export default function HeroAnimations({ start = true }: HeroAnimationsProps) {
  const reduceMotion = useReducedMotion();
  const canAnimate = reduceMotion || start;

  // Mouse parallax for hero glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const glowX  = useSpring(useTransform(mouseX, [0, 1], [-80, 80]), { stiffness: 60, damping: 20 });
  const glowY  = useSpring(useTransform(mouseY, [0, 1], [-60, 60]), { stiffness: 60, damping: 20 });

  const heroRef = useRef<HTMLDivElement>(null);

  function handleMouseMove(e: React.MouseEvent) {
    if (!heroRef.current || reduceMotion) return;
    const { left, top, width, height } = heroRef.current.getBoundingClientRect();
    mouseX.set((e.clientX - left) / width);
    mouseY.set((e.clientY - top) / height);
  }

  return (
    <div ref={heroRef} onMouseMove={handleMouseMove} className="contents relative">

      {/* ── Background Canvas ── */}
      <div className="absolute inset-0 -z-20 overflow-hidden pointer-events-none opacity-50">
         <PlexusBackground />
      </div>

      {/* ── Mouse-following glow ── */}
      {!reduceMotion && (
        <motion.div
          style={{ x: glowX, y: glowY }}
          className="absolute top-1/4 left-1/4 w-[600px] h-[600px] rounded-full bg-sky-600/10 blur-[130px] pointer-events-none -z-10"
        />
      )}

      {/* ── Live status badge ── */}
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.9 }}
        animate={canAnimate ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: -10, scale: 0.9 }}
        transition={{ delay: 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold tracking-wider hover:border-sky-500/40 transition-colors"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative rounded-full h-2 w-2 bg-emerald-500" />
        </span>
        Systems Operational
      </motion.div>

      {/* ── Main headline ── */}
      <motion.div
        initial={{ opacity: 0, y: 24, filter: "blur(10px)" }}
        animate={canAnimate ? { opacity: 1, y: 0, filter: "blur(0px)" } : { opacity: 0, y: 24, filter: "blur(10px)" }}
        transition={{ delay: 0.2, duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
      >
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-[1.15]">
          Engineering Scalable Systems.{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-400">
            Securing Digital Futures.
          </span>
          {" "}Accelerating Technical Talent.
        </h1>
      </motion.div>

      {/* ── Tech stack badges ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={canAnimate ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.35, duration: 0.5 }}
        className="flex flex-wrap gap-2 pt-2"
      >
        {TECH_BADGES.map(({ icon, label, color, border }, i) => (
          <motion.span
            key={label}
            initial={{ opacity: 0, scale: 0.8, y: 12 }}
            animate={canAnimate ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 0.8, y: 12 }}
            transition={{ delay: 0.38 + i * 0.07, type: "spring", stiffness: 260, damping: 20 }}
            whileHover={{ scale: 1.05, y: -2 }}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-gradient-to-r ${color} border ${border} text-slate-300 text-xs font-medium cursor-default shadow-sm backdrop-blur-sm bg-slate-900/40`}
          >
            {icon}{label}
          </motion.span>
        ))}
      </motion.div>

      {/* ── Description ── */}
      <motion.p
        initial={{ opacity: 0, y: 18, filter: "blur(8px)" }}
        animate={canAnimate ? { opacity: 1, y: 0, filter: "blur(0px)" } : { opacity: 0, y: 18, filter: "blur(8px)" }}
        transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mt-5 text-xs sm:text-sm md:text-[15px] text-slate-400 leading-relaxed max-w-lg font-light"
      >
        VAREX is a Cloud Engineering and Talent Acceleration platform focused on
        Architecture, Resilience, and Execution excellence. We deliver DevSecOps consulting,
        SAP SD expertise, and scalable, secure, automated infrastructure solutions for
        startups and enterprises.
      </motion.p>
      
      {/* ── Freelancing motto ── */}
      <motion.p
        initial={{ opacity: 0, x: -16 }}
        animate={canAnimate ? { opacity: 1, x: 0 } : { opacity: 0, x: -16 }}
        transition={{ delay: 0.38, duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
        className="mt-6 text-[11px] sm:text-xs md:text-sm text-slate-300/90 max-w-lg leading-relaxed border-l-2 border-sky-500/40 pl-3.5"
      >
        Goal: <span className="font-extrabold uppercase tracking-wide text-sky-300">Freelancing-first delivery</span>{" "}
        with resilient cloud architectures, stronger security posture, and faster deployment of
        high-impact technical talent for business-critical execution.
      </motion.p>

      {/* ── CTA Buttons ── */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={canAnimate ? { opacity: 1, y: 0 } : { opacity: 0, y: 18 }}
        transition={{ delay: 0.42, duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
        className="flex flex-col sm:flex-row gap-4 pt-4"
      >
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} transition={{ type: "spring", stiffness: 400, damping: 20 }}>
          <Link
            href="/register"
            className="group inline-flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 text-white px-8 py-4 rounded-md font-bold text-sm transition-colors shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:shadow-[0_0_25px_rgba(14,165,233,0.5)]"
          >
            Get Started Free
            <motion.span
              animate={{ x: [0, 4, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            >
              <ArrowRight className="w-4 h-4" />
            </motion.span>
          </Link>
        </motion.div>

        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} transition={{ type: "spring", stiffness: 400, damping: 20 }}>
          <Link
            href="/contact"
            className="group inline-flex items-center justify-center gap-2 bg-transparent hover:bg-white/5 text-white px-8 py-4 rounded-md border border-slate-700 hover:border-slate-500 font-semibold text-sm transition-colors"
          >
            Request a Demo
          </Link>
        </motion.div>
      </motion.div>

    </div>
  );
}
