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
        <div className="absolute inset-0 -z-20 bg-slate-950" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(14,165,233,0.15),transparent)]" />
        <div className="absolute inset-0 -z-10 hero-grid" />
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent -z-10" />

        {/* Floating animated blobs */}
        <div className="absolute top-20 -left-32 w-72 h-72 bg-sky-500/10 rounded-full blur-[100px] animate-blob" />
        <div className="absolute top-40 -right-32 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] animate-blob animation-delay-2000" />
        <div className="absolute -bottom-20 left-1/3 w-64 h-64 bg-brand-500/10 rounded-full blur-[100px] animate-blob animation-delay-4000" />

        <div className="max-w-6xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-16 items-center py-20">
          {/* LEFT: Enhanced animated content */}
          <div className="space-y-8 relative">
            <HeroAnimations start={introDone} />
          </div>

          {/* RIGHT: Hero image */}
          <AnimateIn delay={0.3} direction="right" trigger="mount">
            <div className="relative max-w-[560px] mx-auto lg:mx-0">
              <div className="absolute -inset-4 bg-gradient-to-tr from-sky-500/20 via-indigo-500/10 to-transparent rounded-3xl blur-2xl" />
              <div className="relative rounded-2xl overflow-hidden border border-slate-800 shadow-2xl shadow-sky-900/20">
                <Image
                  src="/hero-cloud-infra.png"
                  alt="VAREX Cloud Infrastructure"
                  width={700}
                  height={450}
                  className="w-full h-auto object-cover"
                  priority
                />
                {/* Overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent" />
              </div>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          TRUST BAR — Key capabilities
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-16 border-y border-slate-800/50 bg-slate-950 rounded-2xl">
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
              <div className="flex items-start gap-5 group">
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
      <section className="relative overflow-hidden py-16 bg-slate-950 rounded-2xl">
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
                <Link href={s.href} className="motion-card group flex flex-col h-full bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-sky-500/40 p-5 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-sky-900/10">
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
      <section className="relative overflow-hidden py-24 bg-slate-900/50 border-y border-slate-800/50 rounded-2xl">
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
      <section className="relative overflow-hidden py-24 bg-slate-950 rounded-2xl">
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
                <div className="motion-card text-center p-8 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-sky-500/30 transition-all duration-300 group">
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
            <div className="relative rounded-3xl overflow-hidden border border-slate-800 bg-gradient-to-r from-sky-950/80 via-slate-900 to-indigo-950/80 p-10 md:p-14 text-center">
              <div className="absolute top-0 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-[120px]" />
              <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-indigo-500/10 rounded-full blur-[100px]" />
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
      <section className="relative overflow-hidden py-24 bg-slate-900/30 border-y border-slate-800/50 rounded-2xl">
        <div className="max-w-6xl mx-auto px-4">
          <Testimonials />
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          NEWSLETTER
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-24 bg-slate-950 rounded-2xl">
        <div className="max-w-6xl mx-auto px-4">
          <NewsletterSignup />
        </div>
      </section>

    </div>
  );
}
