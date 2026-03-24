"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

/**
 * Letter-assembly intro that forms VAREX in full screen.
 * Stays for ~4 seconds or click to skip.
 * Booms (scales up massively and fades out) into the hero section.
 */
export default function VarexIntro() {
  type Phase = "intro" | "exit" | "done";
  const [phase, setPhase] = useState<Phase>("intro");
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    // if (reduceMotion) { setPhase("done"); return; }
    // console.log("useReducedMotion: ", reduceMotion); // Debug
    
    // Uncomment below in production so intro only shows once per session naturally
    // const seen = sessionStorage.getItem("varex-letter-intro-seen");
    // if (seen) { setPhase("done"); return; }

    // Stay for 4 seconds total before booming out
    const exitTimer = setTimeout(() => {
      setPhase("exit");
      // sessionStorage.setItem("varex-letter-intro-seen", "1");
    }, 4000);

    // Completely unmount after an additional 1.5 seconds for the exit animation
    const doneTimer = setTimeout(() => setPhase("done"), 5500);

    return () => { clearTimeout(exitTimer); clearTimeout(doneTimer); };
  }, [reduceMotion]);

  const handleSkip = () => {
    if (phase === "intro") {
      setPhase("exit");
      // sessionStorage.setItem("varex-letter-intro-seen", "1");
    }
  };

  if (phase === "done") return null;

  // Multi-directional starting positions for each letter
  const letterVariants = {
    hidden: (i: number) => {
      const positions = [
        { x: "-100vw", y: "-100vh", rotate: -90 }, // V (Top Left)
        { x: "0",      y: "100vh",  rotate: 45 },  // A (Bottom Center)
        { x: "100vw",  y: "-100vh", rotate: 90 },  // R (Top Right)
        { x: "-100vw", y: "0",      rotate: -45 }, // E (Middle Left)
        { x: "100vw",  y: "100vh",  rotate: 180 }, // X (Bottom Right)
      ];
      return {
        opacity: 0,
        x: positions[i].x,
        y: positions[i].y,
        rotate: positions[i].rotate,
        scale: 0.1
      };
    },
    visible: {
      opacity: 1,
      x: 0,
      y: 0,
      rotate: 0,
      scale: 1,
      transition: { 
        type: "spring" as const, 
        damping: 12, 
        stiffness: 70, 
        mass: 1.5,
        duration: 2 
      }
    }
  };

  const letters = ["V", "A", "R", "E", "X"];

  return (
    <AnimatePresence>
      <motion.div
        key="varex-letter-intro"
        initial={{ opacity: 1 }}
        animate={{ opacity: phase === "exit" ? 0 : 1 }}
        transition={{ duration: phase === "exit" ? 1.0 : 1, ease: "easeInOut" }}
        className="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-slate-950 overflow-hidden"
        style={{ pointerEvents: phase === "exit" ? "none" : "auto" }}
        onClick={handleSkip}
      >
        {/* Subtle grid line overlay giving a tech vibe over the whole background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none" />

        {/* The "Boom" container */}
        <motion.div
          animate={
            phase === "exit"
              ? { scale: 10, opacity: 0, filter: "blur(30px)" } // Massive BOOM effect
              : { scale: 1, opacity: 1, filter: "blur(0px)" }
          }
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative flex flex-col items-center justify-center w-full h-full cursor-pointer"
        >
          {/* Invisible click label */}
          <motion.div 
             initial={{ opacity: 0 }} 
             animate={{ opacity: phase === "intro" ? 0.3 : 0 }} 
             transition={{ delay: 2, duration: 1 }}
             className="absolute top-[15%] text-slate-500 text-sm tracking-widest uppercase animate-pulse"
          >
            Click anywhere to jump
          </motion.div>

          {/* Letters Container */}
          <div className="relative z-10 flex items-center justify-center gap-1 sm:gap-2 md:gap-4 lg:gap-6 select-none">
            {letters.map((char, i) => (
              <motion.span
                key={i}
                custom={i}
                variants={letterVariants}
                initial="hidden"
                animate="visible"
                className="text-[22vw] sm:text-[20vw] md:text-[18vw] lg:text-[16vw] xl:text-[260px] font-extrabold text-white leading-none tracking-tight drop-shadow-[0_0_40px_rgba(14,165,233,0.3)]"
                style={{ fontFamily: "var(--font-lexend, sans-serif)" }}
              >
                {char}
              </motion.span>
            ))}
          </div>

          {/* Subtitle / Tech identity */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.8, duration: 0.8, ease: "easeOut" }}
            className="relative z-10 mt-8 sm:mt-12 text-xs sm:text-sm md:text-base lg:text-xl font-bold tracking-[0.6em] md:tracking-[1em] uppercase text-sky-400 drop-shadow-[0_0_15px_rgba(14,165,233,0.6)]"
          >
            TECH INNOVATION
          </motion.p>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
