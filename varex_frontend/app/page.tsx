"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { CheckCircle2, Shield, Server, Cloud, Blocks, Cpu, Database, BarChart3, Users, Zap, ArrowRight, Box, Network, Terminal, Settings } from "lucide-react";
import AnimateIn, { StaggerContainer, StaggerItem } from "@/components/AnimateIn";
import Testimonials from "@/components/Testimonials";
import NewsletterSignup from "@/components/NewsletterSignup";
import VarexIntro from "@/components/VarexIntro";
import HeroAnimations from "@/components/HeroAnimations";
import FounderSection from "@/components/FounderSection";

export default function HomePage() {
  const [introDone, setIntroDone] = useState(true);

  const featureToneClasses: Record<string, string> = {
    sky: "bg-sky-500/10 text-sky-400",
    indigo: "bg-indigo-500/10 text-indigo-400",
    emerald: "bg-emerald-500/10 text-emerald-400",
    blue: "bg-blue-500/10 text-blue-400",
    violet: "bg-violet-500/10 text-violet-400",
    teal: "bg-teal-500/10 text-teal-400",
  };

  return (
    <div className="flex flex-col gap-6 md:gap-8 pb-4">

      {/* ── Dynamic letter-assembly intro ── */}
      {!introDone && <VarexIntro onComplete={() => setIntroDone(true)} />}

      {/* ═══════════════════════════════════════════════════════════
          NEO-DARK HERO SECTION + TECH STACK MARQUEE
         ═══════════════════════════════════════════════════════════ */}
      <section className={`relative flex flex-col justify-center overflow-hidden px-4 sm:px-6 transform-gpu transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${introDone ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-8 blur-[4px]"}`}>
        
        {/* Abstract Dark Background Elements */}
        <div className="absolute inset-0 z-0 bg-[#020617]" />
        
        {/* Glowing Orbs */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-500/10 blur-[130px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />
        
        {/* Subtle Tech Grid */}
        <div className="absolute inset-0 z-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_15%,transparent_100%)] pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto w-full pt-16 lg:pt-24 pb-16 flex flex-col items-center text-center cursor-default">
          
          {/* Main Hero Content */}
          <div className="space-y-6 flex flex-col items-center max-w-4xl">
            {/* Command Pill */}
            <AnimateIn delay={0.1}>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-sky-400/20 bg-sky-500/10 backdrop-blur-md shadow-[0_0_15px_rgba(14,165,233,0.15)] text-sky-300">
                <span className="flex h-1.5 w-1.5 rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)] animate-pulse" />
                <span className="text-[10px] font-bold tracking-[0.2em] uppercase">Next-Gen DevSecOps & Cloud</span>
              </div>
            </AnimateIn>

            {/* Headline */}
            <AnimateIn delay={0.2}>
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-[2.8rem] font-extrabold text-white tracking-tight leading-tight">
                Architect <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 drop-shadow-sm">Unbreakable</span> Resilience. <span className="text-slate-300">Accelerate Execution.</span>
              </h1>
            </AnimateIn>

            {/* Subtext */}
            <AnimateIn delay={0.3}>
              <p className="text-base sm:text-lg lg:text-xl text-slate-300 max-w-3xl leading-relaxed mx-auto">
                Transform your deployment velocity. We build <span className="text-emerald-300 font-medium tracking-wide">production-grade infrastructure</span>, enforce continuous zero-trust cybersecurity, and deploy elite, AI-vetted engineering teams in days—not months.
              </p>
            </AnimateIn>

            {/* CTA Buttons */}
            <AnimateIn delay={0.4}>
              <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 pb-10">
                <Link href="/services" className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 rounded-full bg-white text-slate-950 font-bold text-sm transition-all hover:bg-slate-200 hover:scale-[1.02] shadow-[0_0_30px_rgba(255,255,255,0.15)] ring-1 ring-white/50">
                  Explore Solutions
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1.5 transition-transform" />
                </Link>
                <Link href="/contact" className="inline-flex items-center justify-center gap-3 px-8 py-4 rounded-full border border-white/10 bg-white/[0.03] text-white font-semibold text-sm transition-all hover:bg-white/[0.08] hover:border-white/20 backdrop-blur-md">
                  Book Architecture Review
                </Link>
              </div>
            </AnimateIn>
          </div>

          {/* Tech Stack Scrolling Marquee - Centered Full Width Below */}
          <AnimateIn delay={0.5} direction="up" className="w-full mt-6">
            <div className="relative w-full max-w-5xl mx-auto">
              
              {/* Premium Glass Container */}
              <div className="relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent backdrop-blur-sm p-4">
                 
                 {/* Marquee Animations */}
                 <style dangerouslySetInnerHTML={{__html: `
                    @keyframes scrollLeft {
                      0% { transform: translateX(0); }
                      100% { transform: translateX(-50%); }
                    }
                    @keyframes scrollRight {
                      0% { transform: translateX(-50%); }
                      100% { transform: translateX(0); }
                    }
                    .animate-scroll-left { animation: scrollLeft 35s linear infinite; }
                    .animate-scroll-right { animation: scrollRight 35s linear infinite; }
                    .animate-scroll-left:hover, .animate-scroll-right:hover { animation-play-state: paused; }
                 `}} />

                 {/* Scrolling Container with Edge Fades */}
                 <div className="relative space-y-5 overflow-hidden py-3" style={{ maskImage: "linear-gradient(to right, transparent, black 15%, black 85%, transparent)", WebkitMaskImage: "linear-gradient(to right, transparent, black 15%, black 85%, transparent)" }}>
                    
                    {/* ROW 1: Scroll Left (Cloud & DevOps) */}
                    <div className="flex w-max animate-scroll-left gap-5">
                       {[
                         { name: "Docker", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original.svg" },
                         { name: "Kubernetes", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/kubernetes/kubernetes-plain.svg" },
                         { name: "AWS", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/amazonwebservices/amazonwebservices-plain-wordmark.svg" },
                         { name: "Azure", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/azure/azure-original.svg" },
                         { name: "GCP", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/googlecloud/googlecloud-original.svg" },
                         { name: "Terraform", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/terraform/terraform-original.svg" },
                         { name: "Ansible", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/ansible/ansible-original.svg" },
                         { name: "Jenkins", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jenkins/jenkins-original.svg" },
                         // Duplicate for seamless scroll
                         { name: "Docker", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original.svg" },
                         { name: "Kubernetes", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/kubernetes/kubernetes-plain.svg" },
                         { name: "AWS", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/amazonwebservices/amazonwebservices-plain-wordmark.svg" },
                         { name: "Azure", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/azure/azure-original.svg" },
                         { name: "GCP", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/googlecloud/googlecloud-original.svg" },
                         { name: "Terraform", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/terraform/terraform-original.svg" },
                         { name: "Ansible", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/ansible/ansible-original.svg" },
                         { name: "Jenkins", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jenkins/jenkins-original.svg" },
                       ].map((tool, i) => (
                          <div key={i} className="flex items-center flex-shrink-0 gap-4 px-6 md:px-8 py-3.5 md:py-4 bg-white/[0.03] border border-white/5 rounded-2xl transition-all shadow-[0_4px_24px_rgba(0,0,0,0.2)] hover:bg-white/[0.08] hover:border-white/20 hover:-translate-y-1">
                             <img src={tool.src} alt={tool.name} className="h-8 md:h-10 w-auto max-w-[70px] md:max-w-[90px] object-contain drop-shadow-[0_0_12px_rgba(255,255,255,0.15)]" />
                             <span className="text-sm md:text-base font-bold text-slate-200 tracking-wide">{tool.name}</span>
                          </div>
                       ))}
                    </div>

                    {/* ROW 2: Scroll Right (SAP, Security, Automation, Data) */}
                    <div className="flex w-max animate-scroll-right gap-5 relative left-[calc(-50%-1.25rem)]">
                       {[
                         { name: "SAP Solutions", src: "https://upload.wikimedia.org/wikipedia/commons/5/59/SAP_2011_logo.svg" },
                         { name: "Cybersecurity (Linux)", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linux/linux-original.svg" },
                         { name: "Security Automation", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" },
                         { name: "SecOps Monitoring", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/prometheus/prometheus-original.svg" },
                         { name: "Observability", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/grafana/grafana-original.svg" },
                         { name: "NGINX Defense", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nginx/nginx-original.svg" },
                         { name: "Enterprise Databases", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg" },
                         { name: "API Security", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postman/postman-original.svg" },
                         // Duplicate for seamless scroll
                         { name: "SAP Solutions", src: "https://upload.wikimedia.org/wikipedia/commons/5/59/SAP_2011_logo.svg" },
                         { name: "Cybersecurity (Linux)", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linux/linux-original.svg" },
                         { name: "Security Automation", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" },
                         { name: "SecOps Monitoring", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/prometheus/prometheus-original.svg" },
                         { name: "Observability", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/grafana/grafana-original.svg" },
                         { name: "NGINX Defense", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nginx/nginx-original.svg" },
                         { name: "Enterprise Databases", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg" },
                         { name: "API Security", src: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postman/postman-original.svg" },
                       ].map((tool, i) => (
                          <div key={i} className="flex items-center flex-shrink-0 gap-4 px-6 md:px-8 py-3.5 md:py-4 bg-white/[0.03] border border-white/5 rounded-2xl transition-all shadow-[0_4px_24px_rgba(0,0,0,0.2)] hover:bg-white/[0.08] hover:border-white/20 hover:-translate-y-1">
                             <img src={tool.src} alt={tool.name} className="h-8 md:h-10 w-auto max-w-[70px] md:max-w-[90px] object-contain drop-shadow-[0_0_12px_rgba(255,255,255,0.15)]" />
                             <span className="text-sm md:text-base font-bold text-slate-200 tracking-wide">{tool.name}</span>
                          </div>
                       ))}
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
      <section className="relative overflow-hidden py-12 sm:py-16 border border-white/5 bg-[linear-gradient(135deg,rgba(5,15,18,0.94),rgba(10,24,19,0.88),rgba(7,14,27,0.92))] rounded-[2rem]">
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
              <div className="glass-panel bento-tile rounded-2xl p-6 flex items-start gap-5 group">
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
      <section className="relative overflow-hidden py-12 sm:py-16 bg-[linear-gradient(180deg,rgba(4,9,9,0.98),rgba(6,10,20,0.96))] rounded-[2rem] border border-white/5">
        <div className="absolute inset-x-0 top-0 h-56 bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.12),transparent_70%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <AnimateIn className="text-center mb-12 lg:mb-16">
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
                <Link href={s.href} className="motion-card group flex flex-col h-full glass-panel bento-tile hover:bg-white/[0.08] border border-white/5 hover:border-emerald-300/30 p-5 rounded-[1.4rem] transition-all duration-300 hover:shadow-xl hover:shadow-emerald-950/10">
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
      <section className="relative overflow-hidden py-16 lg:py-20 bg-[linear-gradient(135deg,rgba(7,16,15,0.92),rgba(7,19,24,0.88),rgba(10,12,22,0.92))] border border-white/5 rounded-[2rem]">
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
      <section className="relative overflow-hidden py-16 lg:py-20 bg-[linear-gradient(180deg,rgba(3,8,8,0.98),rgba(8,11,20,0.96))] rounded-[2rem] border border-white/5">
        <div className="absolute inset-x-0 top-0 h-48 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.12),transparent_70%)]" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-[radial-gradient(circle_at_bottom,rgba(16,185,129,0.1),transparent_72%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <AnimateIn className="text-center mb-12">
            <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-3">Why Choose VAREX</h2>
            <h3 className="text-3xl md:text-5xl font-extrabold text-white">Built for Scale. Designed to Last.</h3>
          </AnimateIn>

          <StaggerContainer className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
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
      <section className="relative overflow-hidden py-16 lg:py-20 bg-[linear-gradient(135deg,rgba(8,14,24,0.9),rgba(14,19,36,0.86))] border border-white/5 rounded-[2rem]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.08),transparent_35%),radial-gradient(circle_at_80%_70%,rgba(168,85,247,0.08),transparent_32%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <Testimonials />
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          NEWSLETTER
         ═══════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden py-16 lg:py-20 bg-[linear-gradient(135deg,rgba(2,6,23,0.96),rgba(10,12,24,0.94),rgba(5,10,10,0.96))] border border-white/5 rounded-[2rem]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.08),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.08),transparent_34%)]" />
        <div className="max-w-6xl mx-auto px-4">
          <NewsletterSignup />
        </div>
      </section>

    </div>
  );
}
