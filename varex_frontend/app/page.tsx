"use client";

import Link from "next/link";
import { motion, Variants } from "framer-motion";
import { ChevronRight, Shield, Server, Box, Cpu, ArrowRight } from "lucide-react";
import Testimonials from "@/components/Testimonials";
import NewsletterSignup from "@/components/NewsletterSignup";

export default function HomePage() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants: Variants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
  };

  return (
    <div className="relative space-y-32 pb-20 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-brand-500/20 blur-[120px] rounded-full opacity-50 pointer-events-none -z-10" />
      <div className="absolute -top-[200px] -right-[200px] w-[600px] h-[600px] bg-varex-blue/10 blur-[150px] rounded-full pointer-events-none -z-10" />

      {/* ── Hero ──────────────────────────────────────────────── */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="grid gap-16 lg:grid-cols-[1.2fr_1fr] items-center pt-16"
      >
        <section className="relative z-10">
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-1.5 text-xs font-semibold text-sky-300 mb-8 backdrop-blur-sm shadow-[0_0_15px_rgba(14,165,233,0.15)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
            </span>
            VAREX &bull; Virtual Architecture, Resilience & Execution
          </motion.div>

          <motion.h1 variants={itemVariants} className="text-5xl sm:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            Secure SaaS infrastructure for <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-brand-500 to-indigo-400 text-glow">the next generation</span>
          </motion.h1>

          <motion.p variants={itemVariants} className="text-slate-300 text-lg mb-10 max-w-xl leading-relaxed">
            VAREX gives you a production-ready foundation: complete authentication, role-based access, and premium content delivery, backed by a resilient <strong className="text-white">FastAPI</strong> core.
          </motion.p>

          <motion.div variants={itemVariants} className="flex flex-wrap gap-4 mb-14">
            <Link href="/register"
              className="group relative inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-brand-600 px-8 py-4 text-sm font-bold text-white shadow-[0_0_40px_-10px_rgba(14,165,233,0.6)] hover:shadow-[0_0_60px_-15px_rgba(14,165,233,0.8)] transition-all duration-300 overflow-hidden">
              <span className="absolute inset-0 w-full h-full -mt-1 rounded-lg opacity-30 bg-gradient-to-b from-transparent via-transparent to-black"></span>
              <span className="relative z-10">Deploy Now</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform relative z-10" />
            </Link>

            <Link href="/dashboard"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700/80 bg-slate-900/50 backdrop-blur-md px-8 py-4 text-sm font-semibold text-slate-200 hover:bg-slate-800 hover:border-sky-500/50 transition-all duration-300">
              View Architecture
            </Link>
          </motion.div>

          <motion.dl variants={containerVariants} className="grid grid-cols-3 gap-6 text-sm text-slate-400 border-t border-slate-800/60 pt-8">
            <motion.div variants={itemVariants} className="space-y-1">
              <dt className="flex items-center gap-1.5 font-bold text-slate-100"><Shield className="w-4 h-4 text-sky-400" /> RBAC</dt>
              <dd className="text-xs leading-relaxed">Granular permissions out of the box.</dd>
            </motion.div>
            <motion.div variants={itemVariants} className="space-y-1">
              <dt className="flex items-center gap-1.5 font-bold text-slate-100"><Server className="w-4 h-4 text-brand-400" /> API-First</dt>
              <dd className="text-xs leading-relaxed">Lightning-fast Python backend routing.</dd>
            </motion.div>
            <motion.div variants={itemVariants} className="space-y-1">
              <dt className="flex items-center gap-1.5 font-bold text-slate-100"><Cpu className="w-4 h-4 text-indigo-400" /> Ready for AI</dt>
              <dd className="text-xs leading-relaxed">Pluggable intelligent evaluation modules.</dd>
            </motion.div>
          </motion.dl>
        </section>

        {/* Live System Card */}
        <motion.section
          variants={itemVariants}
          className="relative perspective-[1000px] xl:ml-10"
        >
          <div className="absolute inset-0 bg-gradient-to-tr from-brand-600/20 to-indigo-500/20 rounded-3xl blur-2xl transform -rotate-6 scale-105 z-0" />

          <div className="relative z-10 glass-card rounded-2xl p-8 border-t-brand-500/30 overflow-hidden transform rotate-2 hover:rotate-0 transition-transform duration-500">
            {/* Animated bg scanline */}
            <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,rgba(14,165,233,0.05)_50%,transparent_100%)] h-[200%] w-full animate-[blob_10s_linear_infinite]" />

            <div className="flex justify-between items-center mb-6 relative z-10 border-b border-slate-800/80 pb-4">
              <h2 className="text-lg font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#34d399]" /> Live Telemetry</h2>
              <span className="font-mono text-xs text-sky-400 bg-sky-950/40 px-3 py-1 rounded-full border border-sky-800/50">Production</span>
            </div>

            <div className="space-y-5 text-sm font-mono text-slate-300 relative z-10">
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">API Endpoint</span>
                <span className="text-emerald-300 flex items-center gap-2">Healthy <span className="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px]">99.9%</span></span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Auth Provider</span>
                <span className="text-slate-100">JWT &bull; FastAPI</span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Region</span>
                <span className="text-slate-100">AWS ap-south-1</span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Latency</span>
                <span className="text-sky-300">~42ms</span>
              </div>
            </div>

            <div className="mt-8 pt-5 border-t border-slate-800/80 grid grid-cols-2 gap-3 relative z-10">
              {[
                { href: "/portfolio", label: "Case Studies" },
                { href: "/workshops", label: "Live Workshops" },
              ].map((l) => (
                <Link key={l.href} href={l.href}
                  className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/30 px-4 py-2.5 text-xs font-semibold
                    text-slate-300 hover:border-sky-500/60 hover:text-sky-300 hover:bg-sky-500/10 transition-all group">
                  {l.label}
                  <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform opacity-50 group-hover:opacity-100" />
                </Link>
              ))}
            </div>
          </div>
        </motion.section>
      </motion.div>

      {/* ── Services Section ────────────────────────────────────── */}
      <section className="space-y-12">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-3">Core Competencies</h2>
          <h3 className="text-3xl md:text-4xl font-extrabold">Engineering & Talent Solutions</h3>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: <Box className="w-8 h-8" />, title: "DevSecOps", desc: "Automated CI/CD pipelines, Kubernetes orchestration, and resilient architecture.", href: "/services/devsecops" },
            { icon: <Shield className="w-8 h-8" />, title: "Cybersecurity", desc: "Continuous threat modeling, penetration testing, and VAPT infrastructure.", href: "/services/cybersecurity" },
            { icon: <Server className="w-8 h-8" />, title: "SAP SD", desc: "Enterprise Sales & Distribution configuration and custom integrations.", href: "/services/sap-sd" },
            { icon: <Cpu className="w-8 h-8" />, title: "AI Hiring", desc: "Deploy pre-vetted engineers using our proprietary AI evaluation matrix.", href: "/services/ai-hiring" },
          ].map((s, idx) => (
            <motion.div
              key={s.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1, type: "spring", stiffness: 50 }}
            >
              <Link href={s.href}
                className="group block h-full glass-card hover:bg-slate-800/60 p-8 rounded-3xl transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-sky-900/30 border-t border-l border-slate-700/50 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-sky-500/10 rounded-full blur-[50px] group-hover:bg-brand-500/20 transition-colors" />
                <div className="text-slate-400 mb-6 group-hover:text-sky-400 transition-colors group-hover:scale-110 origin-left duration-300">
                  {s.icon}
                </div>
                <h4 className="text-xl font-bold text-slate-100 mb-3 group-hover:text-white transition-colors">{s.title}</h4>
                <p className="text-sm text-slate-400 leading-relaxed font-medium">
                  {s.desc}
                </p>
                <div className="mt-6 flex items-center text-xs font-bold text-sky-400 opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all">
                  Explore <ArrowRight className="w-3 h-3 ml-1" />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────── */}
      <Testimonials />

      {/* ── Newsletter ────────────────────────────────────────── */}
      <NewsletterSignup />

    </div>
  );
}