"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { CheckCircle2, Shield, Server, Cloud, Blocks, Cpu, Database, BarChart3, Users, Zap, ArrowRight } from "lucide-react";
import AnimateIn, { StaggerContainer, StaggerItem } from "@/components/AnimateIn";
import Testimonials from "@/components/Testimonials";
import NewsletterSignup from "@/components/NewsletterSignup";
import VarexIntro from "@/components/VarexIntro";
import HeroAnimations from "@/components/HeroAnimations";
import FounderSection from "@/components/FounderSection";

export default function HomePage() {
  const [introDone, setIntroDone] = useState(false);

  const featureToneClasses: Record<string, string> = {
    sky: "bg-sky-500/10 text-sky-400",
    indigo: "bg-indigo-500/10 text-indigo-400",
    emerald: "bg-emerald-500/10 text-emerald-400",
    blue: "bg-blue-500/10 text-blue-400",
    violet: "bg-violet-500/10 text-violet-400",
    teal: "bg-teal-500/10 text-teal-400",
  };

  return (
    <div className="flex flex-col gap-8 md:gap-10 pb-4">

      {/* ── Dynamic letter-assembly intro ── */}
      <VarexIntro onComplete={() => setIntroDone(true)} />

      {/* ═══════════════════════════════════════════════════════════
          HERO SECTION — Full-bleed with animated background
         ═══════════════════════════════════════════════════════════ */}
      <section className={`relative min-h-[90vh] flex items-center overflow-hidden -mx-4 px-4 transform-gpu transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${introDone ? "opacity-100 scale-100 blur-0" : "opacity-0 scale-[1.03] blur-[3px]"}`}>
        {/* Background layers */}
        <div className="absolute inset-0 -z-20 bg-[#020504]" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_50%_at_50%_-12%,rgba(0,255,136,0.14),transparent)]" />
        <div className="absolute inset-0 -z-10 hero-grid" />
        <div className="absolute inset-0 -z-10 command-grid" />
        <div className="absolute inset-x-0 top-24 h-[28rem] -z-10 aurora-band" />
        <div className="absolute left-1/2 top-1/4 h-[22rem] w-[22rem] -translate-x-1/2 -z-10 prism-haze" />
        <svg
          className="absolute inset-0 -z-10 h-full w-full opacity-45 signal-lines"
          viewBox="0 0 1440 900"
          fill="none"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="signalStrokeA" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="rgba(52,211,153,0.0)" />
              <stop offset="45%" stopColor="rgba(52,211,153,0.55)" />
              <stop offset="100%" stopColor="rgba(56,189,248,0.0)" />
            </linearGradient>
            <linearGradient id="signalStrokeB" x1="1" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(99,102,241,0.0)" />
              <stop offset="50%" stopColor="rgba(56,189,248,0.38)" />
              <stop offset="100%" stopColor="rgba(16,185,129,0.0)" />
            </linearGradient>
          </defs>
          <path d="M0 640C190 584 246 476 404 456C528 440 604 506 708 494C844 478 950 332 1088 332C1246 332 1320 436 1440 412" stroke="url(#signalStrokeA)" strokeWidth="1.4" strokeDasharray="8 10" />
          <path d="M64 744C206 684 314 606 434 610C558 614 626 730 760 728C918 726 980 592 1128 560C1224 540 1328 564 1440 630" stroke="url(#signalStrokeB)" strokeWidth="1.2" strokeDasharray="6 14" />
          <circle cx="404" cy="456" r="4" fill="rgba(16,185,129,0.85)" />
          <circle cx="708" cy="494" r="4" fill="rgba(56,189,248,0.75)" />
          <circle cx="1088" cy="332" r="4" fill="rgba(99,102,241,0.72)" />
          <circle cx="434" cy="610" r="3.5" fill="rgba(16,185,129,0.72)" />
          <circle cx="760" cy="728" r="3.5" fill="rgba(56,189,248,0.72)" />
          <circle cx="1128" cy="560" r="3.5" fill="rgba(99,102,241,0.66)" />
        </svg>
        <svg
          className="absolute inset-0 -z-10 h-full w-full opacity-40 varex-topology"
          viewBox="0 0 1440 900"
          fill="none"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="varexTopologyA" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="rgba(0,255,136,0)" />
              <stop offset="50%" stopColor="rgba(0,255,136,0.34)" />
              <stop offset="100%" stopColor="rgba(56,189,248,0)" />
            </linearGradient>
            <linearGradient id="varexTopologyB" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor="rgba(99,102,241,0)" />
              <stop offset="52%" stopColor="rgba(56,189,248,0.28)" />
              <stop offset="100%" stopColor="rgba(158,255,0,0)" />
            </linearGradient>
          </defs>
          <path d="M150 238H354L466 324H640L760 226H960L1088 306H1282" stroke="url(#varexTopologyA)" strokeWidth="1.2" />
          <path d="M220 692H428L544 608H742L872 730H1110L1240 648" stroke="url(#varexTopologyB)" strokeWidth="1.15" />
          <path d="M640 324V516L742 608" stroke="rgba(148,163,184,0.16)" strokeWidth="1" />
          <path d="M760 226V136H1042V306" stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
          <rect x="332" y="220" width="44" height="36" rx="10" fill="rgba(8,15,15,0.64)" stroke="rgba(16,185,129,0.18)" />
          <rect x="618" y="306" width="44" height="36" rx="10" fill="rgba(8,15,15,0.64)" stroke="rgba(56,189,248,0.18)" />
          <rect x="938" y="208" width="44" height="36" rx="10" fill="rgba(8,15,15,0.64)" stroke="rgba(99,102,241,0.18)" />
          <rect x="720" y="590" width="44" height="36" rx="10" fill="rgba(8,15,15,0.64)" stroke="rgba(56,189,248,0.18)" />
          <circle cx="354" cy="238" r="4.5" fill="rgba(0,255,136,0.74)" />
          <circle cx="640" cy="324" r="4.5" fill="rgba(56,189,248,0.7)" />
          <circle cx="760" cy="226" r="4.5" fill="rgba(158,255,0,0.68)" />
          <circle cx="1088" cy="306" r="4.5" fill="rgba(99,102,241,0.72)" />
          <circle cx="742" cy="608" r="4.5" fill="rgba(56,189,248,0.78)" />
          <text x="286" y="208" fill="rgba(148,163,184,0.52)" fontSize="11" letterSpacing="2">EDGE</text>
          <text x="588" y="290" fill="rgba(148,163,184,0.52)" fontSize="11" letterSpacing="2">CI/CD</text>
          <text x="910" y="192" fill="rgba(148,163,184,0.52)" fontSize="11" letterSpacing="2">SECURITY</text>
          <text x="686" y="576" fill="rgba(148,163,184,0.52)" fontSize="11" letterSpacing="2">DELIVERY</text>
        </svg>
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent -z-10" />

        {/* Floating animated blobs */}
        <div className="absolute top-20 -left-32 w-72 h-72 bg-emerald-400/10 rounded-full blur-[100px] animate-blob" />
        <div className="absolute top-40 -right-32 w-80 h-80 bg-lime-300/10 rounded-full blur-[100px] animate-blob animation-delay-2000" />
        <div className="absolute -bottom-20 left-1/3 w-64 h-64 bg-cyan-300/10 rounded-full blur-[100px] animate-blob animation-delay-4000" />
        <div className="absolute top-1/3 left-1/2 w-56 h-56 -translate-x-1/2 rounded-full bg-indigo-500/10 blur-[90px] animate-blob animation-delay-2000" />

        <div className="max-w-6xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-16 items-center py-20">
          {/* LEFT: Enhanced animated content */}
          <div className="space-y-8 relative">
            <div className="space-y-4">
              <span className="terminal-label">Engineering Command Layer</span>
              <div className="glass-panel glass-outline rounded-3xl p-5 md:p-6">
                <div className="grid grid-cols-3 gap-3 text-[11px] uppercase tracking-[0.24em] text-emerald-200/70">
                  <div>
                    <p className="text-white text-2xl font-bold tracking-tight">7 Days</p>
                    <p>Talent Delivery</p>
                  </div>
                  <div>
                    <p className="text-white text-2xl font-bold tracking-tight">12x</p>
                    <p>Release Velocity</p>
                  </div>
                  <div>
                    <p className="text-white text-2xl font-bold tracking-tight">Zero</p>
                    <p>Chaos by Default</p>
                  </div>
                </div>
              </div>
            </div>
            <HeroAnimations start={introDone} />
          </div>

          {/* RIGHT: Hero image */}
          <AnimateIn delay={0.3} direction="right" trigger="mount">
            <div className="relative max-w-[560px] mx-auto lg:mx-0">
              <div className="absolute -inset-4 bg-gradient-to-tr from-emerald-400/20 via-lime-300/8 to-transparent rounded-3xl blur-2xl" />
              <div className="absolute -inset-[1px] rounded-[1.6rem] bg-gradient-to-br from-emerald-300/30 via-white/10 to-transparent opacity-80" />
              <div className="absolute left-5 top-5 z-10 rounded-2xl border border-emerald-300/15 bg-slate-950/55 px-4 py-3 backdrop-blur-md">
                <p className="text-[10px] uppercase tracking-[0.28em] text-emerald-200/65">Execution Fabric</p>
                <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-300">
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,0.6)]" />
                  Cloud
                  <span className="inline-block h-2 w-2 rounded-full bg-sky-400 shadow-[0_0_14px_rgba(56,189,248,0.6)]" />
                  Security
                  <span className="inline-block h-2 w-2 rounded-full bg-lime-300 shadow-[0_0_14px_rgba(190,242,100,0.5)]" />
                  Talent
                </div>
              </div>
              <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl shadow-emerald-950/20">
                <Image
                  src="/hero-cloud-infra.png"
                  alt="VAREX Cloud Infrastructure"
                  width={700}
                  height={450}
                  className="w-full h-auto object-cover"
                  priority
                />
                {/* Overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#020504]/70 via-transparent to-transparent" />
                <svg
                  className="absolute inset-x-0 top-0 z-[1] h-full w-full opacity-55 varex-topology"
                  viewBox="0 0 700 450"
                  fill="none"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path d="M42 116H184L252 178H356L428 110H562L648 164" stroke="rgba(56,189,248,0.32)" strokeWidth="1.2" />
                  <path d="M70 320H214L300 264H430L508 336H644" stroke="rgba(16,185,129,0.26)" strokeWidth="1.2" />
                  <path d="M356 178V264" stroke="rgba(148,163,184,0.16)" strokeWidth="1" />
                  <circle cx="184" cy="116" r="4.2" fill="rgba(16,185,129,0.76)" />
                  <circle cx="356" cy="178" r="4.2" fill="rgba(56,189,248,0.72)" />
                  <circle cx="428" cy="110" r="4.2" fill="rgba(190,242,100,0.72)" />
                  <circle cx="508" cy="336" r="4.2" fill="rgba(99,102,241,0.72)" />
                </svg>
                <div className="absolute left-4 right-4 bottom-4 glass-panel rounded-2xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-200/70 mb-2">Active Delivery Lanes</p>
                  <div className="grid grid-cols-2 gap-3 text-sm text-slate-200">
                    <div className="rounded-xl bg-white/5 p-3">Cloud modernization</div>
                    <div className="rounded-xl bg-white/5 p-3">DevSecOps hardening</div>
                    <div className="rounded-xl bg-white/5 p-3">AI hiring automation</div>
                    <div className="rounded-xl bg-white/5 p-3">SAP enterprise delivery</div>
                  </div>
                </div>
              </div>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          TRUST BAR — Key capabilities
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-16 border border-white/5 bg-[linear-gradient(135deg,rgba(5,15,18,0.94),rgba(10,24,19,0.88),rgba(7,14,27,0.92))] rounded-[2rem]">
        <div className="absolute inset-y-0 left-0 w-1/2 bg-[radial-gradient(circle_at_left_center,rgba(52,211,153,0.08),transparent_70%)]" />
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_right_center,rgba(56,189,248,0.08),transparent_70%)]" />
        <StaggerContainer className="max-w-6xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 gap-8">
          {[
            {
              icon: <Server className="w-6 h-6" />,
              color: "sky",
              title: "Freelancing-Ready Engineering Delivery",
              desc: "Apply production-grade DevOps, cloud architecture, and automation workflows used in real enterprise engagements.",
            },
            {
              icon: <Shield className="w-6 h-6" />,
              color: "indigo",
              title: "Practical Resilience & Security Frameworks",
              desc: "Implement scalable, secure, and compliant infrastructure patterns built for reliability under real workload pressure.",
            },
            {
              icon: <BarChart3 className="w-6 h-6" />,
              color: "emerald",
              title: "Structured Skill Acceleration",
              desc: "Strengthen practical capability through guided milestones, hands-on validation, and expert-led feedback loops.",
            },
            {
              icon: <Cpu className="w-6 h-6" />,
              color: "blue",
              title: "AI-Powered Interview Platform",
              desc: "Two modes: Mock Interviews for candidate practice with instant AI feedback, and AI Interviews for clients — automated enterprise-grade assessments.",
            },
          ].map((f) => (
            <StaggerItem key={f.title}>
              <div className="glass-panel rounded-2xl p-6 flex items-start gap-5 group">
                <div className={`flex-shrink-0 p-3.5 rounded-xl group-hover:scale-110 transition-transform duration-300 ${featureToneClasses[f.color]}`}>
                  {f.icon}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-1.5">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          SERVICES SECTION — What We Do
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-16 bg-[linear-gradient(180deg,rgba(4,9,9,0.98),rgba(6,10,20,0.96))] rounded-[2rem] border border-white/5">
        <div className="absolute inset-x-0 top-0 h-56 bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.12),transparent_70%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <AnimateIn className="text-center mb-16">
            <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-3">What We Do</h2>
            <h3 className="text-3xl md:text-5xl font-extrabold text-white mb-4">Comprehensive Engineering Solutions</h3>
            <p className="text-slate-400 max-w-2xl mx-auto">
              From CI/CD pipelines to threat-resilient production environments, we handle the full spectrum of modern infrastructure challenges.
            </p>
          </AnimateIn>

          <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" staggerDelay={0.08}>
            {[
              { icon: <Blocks className="w-5 h-5" />, title: "CI/CD Pipeline Setup", desc: "Automated code build, testing, and deployment pipelines using Jenkins and GitHub Actions.", href: "/services/ci-cd-pipeline-setup", color: "blue" },
              { icon: <Cloud className="w-5 h-5" />, title: "Cloud Infrastructure Setup", desc: "Secure, scalable AWS, Azure, and GCP infrastructure provisioning with IaC.", href: "/services/cloud-infrastructure-automation", color: "sky" },
              { icon: <Server className="w-5 h-5" />, title: "Container Orchestration", desc: "Docker and Kubernetes setup for scalable, containerized application deployments.", href: "/services/containerization-orchestration", color: "indigo" },
              { icon: <BarChart3 className="w-5 h-5" />, title: "Monitoring Solutions", desc: "Real-time monitoring and log management with Prometheus, Grafana, and Loki.", href: "/services/monitoring-logging-solutions", color: "teal" },
              { icon: <Shield className="w-5 h-5" />, title: "DevSecOps Implementation", desc: "Security scanning and compliance integration embedded directly into CI/CD pipelines.", href: "/services/devsecops-implementation", color: "emerald" },
              { icon: <Database className="w-5 h-5" />, title: "Capacity Planning", desc: "Performance and cost optimization for cloud, Kubernetes, and on-prem infrastructure.", href: "/services/capacity-planning-optimization", color: "violet" },
              { icon: <BarChart3 className="w-5 h-5" />, title: "FinOps & Cost Governance", desc: "Cloud cost visibility, budgeting controls, and spend optimization.", href: "/services/finops-cost-governance", color: "sky" },
              { icon: <Shield className="w-5 h-5" />, title: "Cybersecurity", desc: "Continuous threat modeling, penetration testing, and compliance frameworks.", href: "/services/cybersecurity", color: "indigo" },
              { icon: <Database className="w-5 h-5" />, title: "SAP Solutions", desc: "SAP consulting, implementation support, and integration aligned to enterprise workflows.", href: "/services/sap-solutions", color: "blue" },
              { icon: <Cpu className="w-5 h-5" />, title: "AI-Powered Hiring", desc: "Deploy pre-vetted engineers in 7 days using our proprietary evaluation matrix.", href: "/services/ai-powered-hiring", color: "emerald" },
            ].map((s) => (
              <StaggerItem key={s.title}>
                <Link href={s.href} className="motion-card group flex flex-col h-full glass-panel hover:bg-white/[0.08] border border-white/5 hover:border-emerald-300/30 p-5 rounded-[1.4rem] transition-all duration-300 hover:shadow-xl hover:shadow-emerald-950/10">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 ${featureToneClasses[s.color]}`}>
                    {s.icon}
                  </div>
                  <h4 className="text-[15px] font-bold text-slate-200 mb-2 group-hover:text-white transition-colors">{s.title}</h4>
                  <p className="text-[13px] text-slate-400 leading-relaxed mb-4 flex-grow">{s.desc}</p>
                  <span className="inline-flex items-center text-xs font-semibold text-sky-400 opacity-60 group-hover:opacity-100 transition-all duration-300 mt-auto">
                    Learn more <ArrowRight className="w-3.5 h-3.5 ml-1.5 group-hover:translate-x-1 transition-transform" />
                  </span>
                </Link>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          ABOUT SECTION — with image
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-24 bg-[linear-gradient(135deg,rgba(7,16,15,0.92),rgba(7,19,24,0.88),rgba(10,12,22,0.92))] border border-white/5 rounded-[2rem]">
        <div className="absolute -left-24 top-10 h-72 w-72 rounded-full bg-emerald-400/10 blur-[120px]" />
        <div className="absolute right-0 bottom-0 h-72 w-72 rounded-full bg-cyan-400/10 blur-[120px]" />
        <div className="max-w-6xl mx-auto px-4 flex flex-col lg:flex-row items-center gap-16">
          {/* Left: Content */}
          <div className="lg:w-1/2 space-y-6">
            <AnimateIn>
              <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase">About VAREX</h2>
            </AnimateIn>
            <AnimateIn delay={0.1}>
                <h3 className="text-3xl md:text-4xl font-extrabold text-white leading-tight">
                Empowering scalable, secure digital transformations.
              </h3>
            </AnimateIn>
            <AnimateIn delay={0.2}>
              <p className="text-slate-400 leading-relaxed text-base">
                We are a dedicated team of cloud architects, security researchers, and software engineers on a mission to bring
                enterprise-grade tooling to businesses of all sizes. From automated container orchestration to deep SAP functional
                knowledge, we build architectures designed to last.
              </p>
            </AnimateIn>

            <StaggerContainer className="space-y-3 pt-4" staggerDelay={0.08} delayChildren={0.3}>
              {[
                "Modern Containerization & Kubernetes Orchestration",
                "Advanced Monitoring, Logging & Observability Solutions",
                "Cloud Migration, Modernization & Cost Optimization",
                "AI-Powered Mock & Client Interview Platform",
                "DevSecOps Implementation & Security Hardening",
              ].map((item) => (
                <StaggerItem key={item}>
                  <div className="flex items-center gap-3 text-slate-300 text-sm">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span>{item}</span>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>

            <AnimateIn delay={0.5}>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mt-8 pt-4 border-t border-slate-800/50">
                <Link href="/about" className="group flex items-center gap-4 p-2 pr-5 rounded-full border border-slate-800 bg-slate-900/50 hover:bg-slate-800 hover:border-sky-500/30 transition-all shadow-lg hover:shadow-sky-900/20">
                  <Image
                    src="/founder.jpg"
                    width={48} height={48}
                    className="rounded-full object-cover border-2 border-slate-700 group-hover:border-sky-500/50 transition-colors h-12 w-12"
                    alt="Sai Charitha Chinthakunta"
                  />
                  <div>
                    <p className="text-sm font-bold text-white group-hover:text-sky-100 transition-colors">Sai Charitha Chinthakunta</p>
                    <p className="text-xs text-sky-400 font-medium">Founder & CEO</p>
                  </div>
                </Link>

                <Link href="/team" className="inline-flex items-center gap-2 text-sky-400 hover:text-sky-300 font-semibold text-sm group">
                  Meet Our Team <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </AnimateIn>
          </div>

          {/* Right: Image */}
          <AnimateIn delay={0.2} direction="right" className="lg:w-1/2 w-full">
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-bl from-sky-500/15 to-indigo-500/10 rounded-3xl blur-2xl" />
              <div className="relative rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
                <Image
                  src="/about-team-collab.png"
                  alt="VAREX Team Collaboration"
                  width={600}
                  height={400}
                  className="w-full h-auto object-cover"
                />
              </div>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          WHY VAREX — Numbers & CTA
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-24 bg-[linear-gradient(180deg,rgba(3,8,8,0.98),rgba(8,11,20,0.96))] rounded-[2rem] border border-white/5">
        <div className="absolute inset-x-0 top-0 h-48 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.12),transparent_70%)]" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-[radial-gradient(circle_at_bottom,rgba(16,185,129,0.1),transparent_72%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <AnimateIn className="text-center mb-16">
            <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-3">Why Choose VAREX</h2>
            <h3 className="text-3xl md:text-5xl font-extrabold text-white">Built for Scale. Designed to Last.</h3>
          </AnimateIn>

          <StaggerContainer className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {[
              { icon: <Users className="w-7 h-7" />, value: "50+", label: "Enterprise Clients" },
              { icon: <Zap className="w-7 h-7" />, value: "99.9%", label: "Uptime SLA" },
              { icon: <BarChart3 className="w-7 h-7" />, value: "12x", label: "Faster Deployments" },
              { icon: <Shield className="w-7 h-7" />, value: "0", label: "Security Breaches" },
            ].map((s) => (
              <StaggerItem key={s.label}>
                <div className="motion-card text-center p-8 rounded-[1.6rem] glass-panel border border-white/5 hover:border-emerald-300/25 transition-all duration-300 group">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-sky-500/10 text-sky-400 mb-4 group-hover:scale-110 transition-transform">
                    {s.icon}
                  </div>
                  <p className="text-3xl font-extrabold text-white mb-1">{s.value}</p>
                  <p className="text-sm text-slate-400">{s.label}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>

          {/* CTA Banner */}
          <AnimateIn>
            <div className="relative rounded-[2rem] overflow-hidden border border-white/10 bg-[linear-gradient(135deg,rgba(6,20,16,0.95),rgba(10,28,20,0.88),rgba(5,10,10,0.95))] p-10 md:p-14 text-center">
              <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-400/10 rounded-full blur-[120px]" />
              <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-lime-300/10 rounded-full blur-[100px]" />
              <div className="relative z-10">
                <Cpu className="w-12 h-12 text-sky-400 mx-auto mb-6" />
                <h4 className="text-2xl md:text-3xl font-extrabold text-white mb-4">
                  AI-Powered Interviews — No Human Bottlenecks
                </h4>
                <p className="text-slate-400 max-w-lg mx-auto mb-8">
                  Our AI Interview Platform offers two modes: Mock Interviews for candidates to practice and get instant feedback,
                  and AI Interviews for Clients — fully automated enterprise-grade technical assessments at scale.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <Link href="/hire" className="motion-button inline-flex items-center gap-2 bg-white text-slate-900 hover:bg-slate-100 px-8 py-3.5 rounded-xl text-sm font-bold transition-all shadow-lg">
                    Explore Talent Solutions <ArrowRight className="w-4 h-4" />
                  </Link>
                  <Link href="/ai-interview" className="motion-button inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-white px-8 py-3.5 rounded-xl text-sm font-semibold transition-all">
                    Open AI Interview App
                  </Link>
                  <Link href="/contact" className="motion-button inline-flex items-center gap-2 border border-slate-600 hover:border-sky-500 text-white px-8 py-3.5 rounded-xl text-sm font-semibold transition-all">
                    Book Free Consultation
                  </Link>
                </div>
              </div>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          TESTIMONIALS
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-24 bg-[linear-gradient(135deg,rgba(8,14,24,0.9),rgba(14,19,36,0.86))] border-y border-slate-800/50 rounded-2xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.08),transparent_35%),radial-gradient(circle_at_80%_70%,rgba(168,85,247,0.08),transparent_32%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <Testimonials />
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          NEWSLETTER
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-24 bg-[linear-gradient(135deg,rgba(2,6,23,0.96),rgba(10,12,24,0.94),rgba(5,10,10,0.96))] rounded-2xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.08),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.08),transparent_34%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <NewsletterSignup />
        </div>
      </section>

    </div>
  );
}
