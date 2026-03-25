"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";

type VarexIntroProps = {
  onComplete?: () => void;
};

export default function VarexIntro({ onComplete }: VarexIntroProps) {
  type Phase = "assemble" | "hold" | "boom" | "done";
  const [phase, setPhase] = useState<Phase>("assemble");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const completeIntro = useCallback(() => {
    if (phase !== "done") {
      setPhase("done");
      onComplete?.();
    }
  }, [onComplete, phase]);

  useEffect(() => {
    if (phase === "assemble") {
      const timer = setTimeout(() => setPhase("hold"), 1500);
      return () => clearTimeout(timer);
    }
    if (phase === "hold") {
      const timer = setTimeout(() => setPhase("boom"), 5000);
      return () => clearTimeout(timer);
    }
    if (phase === "boom") {
      const timer = setTimeout(() => completeIntro(), 850);
      return () => clearTimeout(timer);
    }
  }, [completeIntro, phase]);

  const handleSkip = () => {
    if (phase !== "done") {
      setPhase("boom");
    }
  };

  if (phase === "done" || !mounted) return null;

  const letters = ["V", "A", "R", "E", "X"];

  const letterVariants = {
    hidden: (i: number) => {
      const positions = [
        { x: -420, y: -340, rotate: -55, scale: 0.35 },
        { x: 0, y: 340, rotate: 40, scale: 0.35 },
        { x: 420, y: -320, rotate: 55, scale: 0.35 },
        { x: -380, y: 0, rotate: -35, scale: 0.35 },
        { x: 420, y: 300, rotate: 90, scale: 0.35 },
      ];
      return {
        opacity: 0,
        ...positions[i],
      };
    },
    assemble: (i: number) => ({
      opacity: 1,
      x: 0,
      y: 0,
      rotate: 0,
      scale: 1,
      transition: {
        type: "spring" as const,
        stiffness: 120,
        damping: 14,
        mass: 0.85,
        delay: i * 0.08,
      },
      transitionEnd: {
        x: 0,
        y: 0,
        rotate: 0,
        scale: 1,
      },
    }),
    hold: {
      opacity: 1,
      x: 0,
      y: 0,
      rotate: 0,
      scale: 1,
      filter: "blur(0px)",
    },
  };

  return createPortal(
    <AnimatePresence>
      <motion.div
        key="varex-letter-intro"
        initial={{ opacity: 1 }}
        animate={{ opacity: phase === "boom" ? 0 : 1 }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
        className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-slate-950 overflow-hidden"
        style={{ pointerEvents: phase === "boom" ? "none" : "auto" }}
        onClick={handleSkip}
      >
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none" />

        <motion.div
          animate={
            phase === "boom"
              ? { scale: 8, opacity: 0 }
              : { scale: 1, opacity: 1 }
          }
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="relative flex flex-col items-center justify-center w-full h-full"
          style={{ willChange: "transform, opacity" }}
        >
          {/* Skip hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: phase === "assemble" || phase === "hold" ? 1 : 0 }}
            transition={{ delay: 1, duration: 1 }}
            className="absolute top-[14%] text-slate-500 text-[11px] sm:text-xs tracking-[0.24em] uppercase animate-pulse"
          >
            Tap anywhere to skip
          </motion.div>

          {/* Intro container */}
          <div className="relative z-10 w-[min(86vw,940px)] px-5 sm:px-10 py-8 sm:py-12 rounded-[28px] border border-sky-500/30 bg-[radial-gradient(80%_120%_at_50%_0%,rgba(14,165,233,0.2),rgba(2,6,23,0.85)),linear-gradient(180deg,rgba(15,23,42,0.95),rgba(2,6,23,0.92))] shadow-[0_0_100px_rgba(14,165,233,0.16)]">
            <div className="pointer-events-none absolute inset-0 rounded-[28px] ring-1 ring-white/10" />

            <div className="relative flex items-center justify-center gap-1 sm:gap-2 md:gap-4 lg:gap-6 select-none">
              {letters.map((char, i) => (
                <motion.span
                  key={i}
                  custom={i}
                  variants={letterVariants}
                  initial="hidden"
                  animate={phase === "assemble" ? "assemble" : "hold"}
                  className="text-[17vw] sm:text-[15vw] md:text-[13vw] lg:text-[12vw] xl:text-[180px] font-extrabold text-white leading-none tracking-tight drop-shadow-[0_0_40px_rgba(14,165,233,0.3)] inline-block"
                  style={{ fontFamily: "var(--font-lexend, sans-serif)", willChange: "transform, opacity" }}
                >
                  {char}
                </motion.span>
              ))}
            </div>
          </div>

          {/* Subtitle / taglines */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{
              opacity: phase === "hold" ? 1 : 0,
              y: phase === "hold" ? 0 : 30,
            }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="relative z-10 mt-8 sm:mt-12 text-xs sm:text-sm md:text-base lg:text-xl font-bold tracking-[0.6em] md:tracking-[1em] uppercase text-sky-400 drop-shadow-[0_0_15px_rgba(14,165,233,0.6)]"
            style={{ willChange: "transform, opacity" }}
          >
            TECH INNOVATION
          </motion.p>
        </motion.div>

        {/* Global effects over the letters */}
        <motion.div
          animate={
            phase === "boom"
              ? { scale: [1, 5, 8], opacity: [1, 0.4, 0] }
              : { scale: 1, opacity: 1 }
          }
          transition={{ duration: 0.8, ease: "easeIn" }}
          className="pointer-events-none absolute h-[54vmax] w-[54vmax] rounded-full bg-[radial-gradient(circle,rgba(14,165,233,0.6)_0%,rgba(14,165,233,0.15)_42%,rgba(2,6,23,0)_72%)] mix-blend-screen"
          style={{ willChange: "transform, opacity" }}
        />
      </motion.div>
    </AnimatePresence>,
    document.body
  );
}
