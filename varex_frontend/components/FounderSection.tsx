"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BadgeCheck, BriefcaseBusiness, Quote } from "lucide-react";
import AnimateIn, { StaggerContainer, StaggerItem } from "@/components/AnimateIn";

export default function FounderSection() {
  return (
    <section className="relative overflow-hidden py-24 bg-slate-950 border-y border-slate-800/50 rounded-2xl">
      <div className="max-w-6xl mx-auto px-4 flex flex-col lg:flex-row items-center gap-16">
        
        {/* Left: Founder Image */}
        <AnimateIn direction="left" className="lg:w-5/12 w-full">
          <div className="relative max-w-[420px] mx-auto lg:mx-0">
            {/* Background Glow */}
            <div className="absolute -inset-4 bg-gradient-to-tr from-indigo-500/20 via-sky-500/10 to-transparent rounded-3xl blur-2xl" />
            
            {/* Decorative Frame */}
            <div className="relative rounded-2xl overflow-hidden border border-slate-800 shadow-2xl shadow-sky-900/20 aspect-[4/5] bg-slate-900">
              <Image
                src="/founder.jpg"
                alt="Sai Charitha Chinthakunta - VAREX Founder"
                fill
                className="object-cover object-center grayscale hover:grayscale-0 transition-all duration-700"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 420px"
              />
              {/* Overlay Gradient for Text Readability if needed */}
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-80" />
              
              <div className="absolute bottom-6 left-6 right-6">
                <Quote className="w-8 h-8 text-sky-400 opacity-50 mb-2" />
                <p className="text-sm text-slate-200 font-semibold italic">
                  &quot;Resilience in architecture and excellence in execution are the true differentiators in enterprise transformations.&quot;
                </p>
              </div>
            </div>
            
            {/* Status floating badge */}
            <div className="absolute -right-4 top-12 bg-slate-900/90 backdrop-blur-md border border-slate-700/50 p-4 rounded-2xl shadow-xl shadow-black/50">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-500/10 text-blue-400">
                  <BriefcaseBusiness className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium tracking-wide">Expertise</p>
                  <p className="text-sm text-white font-bold">SAP SD Architect</p>
                </div>
              </div>
            </div>
          </div>
        </AnimateIn>

        {/* Right: Content */}
        <div className="lg:w-7/12 space-y-6">
          <AnimateIn>
            <h2 className="text-sm font-bold tracking-widest text-indigo-400 uppercase flex items-center gap-2">
              <span className="w-8 h-px bg-indigo-400/50 inline-block"></span>
              Meet The Founder
            </h2>
          </AnimateIn>
          
          <AnimateIn delay={0.1}>
            <h3 className="text-3xl md:text-5xl font-extrabold text-white leading-tight">
              Sai Charitha Chinthakunta
            </h3>
            <p className="text-sky-400 text-lg mt-2 font-medium">Founder & CEO, VAREX</p>
          </AnimateIn>
          
          <AnimateIn delay={0.2} className="space-y-4">
            <p className="text-slate-400 leading-relaxed text-base">
              With a deep specialization in <strong className="text-slate-200">SAP Sales & Distribution (SD)</strong> and large-scale enterprise deployments, Sai Charitha founded VAREX to bridge the gap between rigorous enterprise software practices and agile cloud infrastructure. 
            </p>
            <p className="text-slate-400 leading-relaxed text-base">
              Her extensive experience driving complex SAP implementations has shaped VAREX's core philosophy: that scalable, secure architecture is built on a foundation of operational resilience and deep functional domain knowledge. Under her leadership, VAREX is accelerating the way technical talent and cloud infrastructure are deployed at scale.
            </p>
          </AnimateIn>

          <StaggerContainer className="flex flex-wrap gap-3 pt-4" staggerDelay={0.08} delayChildren={0.3}>
            {[
              "Enterprise SAP SD Transformations",
              "Strategic Cloud Architecture",
              "Operational Resilience",
              "Technical Talent Acceleration",
            ].map((skill) => (
              <StaggerItem key={skill}>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold shadow-sm hover:border-slate-600 transition-colors">
                  <BadgeCheck className="w-4 h-4 text-sky-400" />
                  {skill}
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>

          <AnimateIn delay={0.6}>
            <div className="pt-6 mt-6 border-t border-slate-800/50">
              <Link href="https://www.linkedin.com/company/varextech" target="_blank" className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-6 py-3 rounded-lg text-sm font-semibold text-white transition-all shadow-md group">
                Connect on LinkedIn
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </AnimateIn>
        </div>

      </div>
    </section>
  );
}
