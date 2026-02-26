"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Shield, Server, Cloud, Blocks, Cpu, Database } from "lucide-react";
import Testimonials from "@/components/Testimonials";
import NewsletterSignup from "@/components/NewsletterSignup";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-24 pb-20">

      {/* ── Hero Section ──────────────────────────────────────── */}
      <section className="relative pt-20 pb-12 lg:pt-32 lg:pb-24 border-b border-slate-800/50">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-900/20 via-slate-950 to-slate-950"></div>
        <div className="max-w-4xl mx-auto text-center px-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold uppercase tracking-wider mb-6">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></span>
            Enterprise SaaS Infrastructure
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight leading-tight mb-6">
            Accelerating Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-400">DevOps & Cloud</span> Journey With Confidence
          </h1>

          <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            VAREX provides a production-ready, highly secure foundation equipped with complete authentication, granular role-based access, and premium content delivery—all backed by a resilient FastAPI core.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 text-white px-8 py-3.5 rounded-lg font-semibold transition-all shadow-lg shadow-sky-500/20">
              Deploy Your Infrastructure
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-8 py-3.5 rounded-lg border border-slate-700 font-semibold transition-all">
              View Architecture
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features List (Trust Bar) ───────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 w-full">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 py-8 border-y border-slate-800/50">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-sky-500/10 text-sky-400"><Shield className="w-6 h-6" /></div>
            <div>
              <h3 className="text-slate-200 font-bold mb-1">Granular RBAC</h3>
              <p className="text-sm text-slate-400">Guest, free, premium, and admin role enforcement out of the box.</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400"><Server className="w-6 h-6" /></div>
            <div>
              <h3 className="text-slate-200 font-bold mb-1">API-First Design</h3>
              <p className="text-sm text-slate-400">Lightning fast Python backend routing with robust JWT Authentication.</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400"><Cpu className="w-6 h-6" /></div>
            <div>
              <h3 className="text-slate-200 font-bold mb-1">Ready for AI</h3>
              <p className="text-sm text-slate-400">Pluggable intelligent evaluation modules for screening and analytics.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── What We Do (Services Section) ─────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 w-full">
        <div className="text-center mb-16">
          <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase mb-3">What We Do</h2>
          <h3 className="text-3xl md:text-4xl font-extrabold text-white">Comprehensive Engineering Solutions</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[
            { icon: <Cloud className="w-6 h-6" />, title: "Cloud Infrastructure Setup", desc: "Automated provisioning and scaling of robust AWS/Azure environments using IaC.", href: "/services/devsecops" },
            { icon: <Blocks className="w-6 h-6" />, title: "CI/CD Pipeline Automation", desc: "Seamless integration and deployment paths utilizing modern DevSecOps tools.", href: "/services/devsecops" },
            { icon: <Shield className="w-6 h-6" />, title: "Cybersecurity & VAPT", desc: "Continuous threat modeling, compliance checks, and infrastructure hardening.", href: "/services/cybersecurity" },
            { icon: <Database className="w-6 h-6" />, title: "SAP SD Integration", desc: "Enterprise Sales & Distribution configurations and module optimization.", href: "/services/sap-sd" },
          ].map((s) => (
            <Link key={s.title} href={s.href} className="group block h-full bg-slate-900/50 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/50 p-6 rounded-2xl transition-all">
              <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 group-hover:text-sky-400 group-hover:bg-sky-500/10 transition-colors mb-5">
                {s.icon}
              </div>
              <h4 className="text-lg font-bold text-slate-200 mb-2">{s.title}</h4>
              <p className="text-sm text-slate-400 leading-relaxed mb-4">{s.desc}</p>
              <div className="flex items-center text-sm font-semibold text-sky-400 group-hover:text-sky-300">
                Learn more <ArrowRight className="w-4 h-4 ml-1 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── About Us Component ────────────────────────────────── */}
      <section className="bg-slate-900 border-y border-slate-800">
        <div className="max-w-6xl mx-auto px-4 py-20 flex flex-col md:flex-row items-center gap-12">
          <div className="md:w-1/2 space-y-6">
            <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase">About VAREX</h2>
            <h3 className="text-3xl font-bold text-white leading-tight">Empowering scalable, secure digital transformations.</h3>
            <p className="text-slate-400 leading-relaxed">
              We are a dedicated team of cloud architects, security researchers, and software engineers on a mission to bring enterprise-grade tooling to businesses of all sizes. From automated container orchestration to deep SAP functional knowledge, we build architectures designed to last.
            </p>
            <ul className="space-y-3 pt-4">
              {[
                "Modern Containerization & Orchestration",
                "Advanced Monitoring & Logging Solutions",
                "Migration, Modernization & Optimization",
                "Proprietary AI Engineer Vetting"
              ].map(item => (
                <li key={item} className="flex items-center gap-3 text-slate-300 text-sm">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" /> {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="md:w-1/2 w-full">
            <div className="rounded-2xl border border-slate-700 bg-slate-950 p-8 shadow-2xl relative overflow-hidden flex flex-col items-center text-center justify-center">
              <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/10 blur-[60px] rounded-full"></div>
              <Cpu className="w-16 h-16 text-sky-400 mb-6" />
              <h4 className="text-xl font-bold text-white mb-2">Need to hire top-tier talent?</h4>
              <p className="text-sm text-slate-400 mb-6">
                Are you open to engaging pre-vetted freelance, remote, or full-time engineers? Our AI-powered screening process delivers talent in just 7 days.
              </p>
              <Link href="/hire" className="bg-white text-slate-900 hover:bg-slate-200 px-6 py-2.5 rounded-lg text-sm font-bold transition-colors">
                Explore Talent Solutions
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Testimonials & Newsletter ─────────────────────────── */}
      <div className="space-y-24">
        <Testimonials />
        <NewsletterSignup />
      </div>

    </div>
  );
}