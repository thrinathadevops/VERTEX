"use client";

import { useState } from "react";
import AnimateIn, { StaggerContainer, StaggerItem } from "@/components/AnimateIn";

interface Testimonial {
  name: string;
  role: string;
  company: string;
  avatar: string;
  content: string;
  rating: number;
  category: "devops" | "security" | "sap" | "hiring" | "workshop";
}

const TESTIMONIALS: Testimonial[] = [
  {
    name: "Arjun Mehta",
    role: "VP Engineering",
    company: "FinTech Startup, Bengaluru",
    avatar: "AM",
    content: "VAREX rebuilt our entire CI/CD pipeline in 3 weeks. Zero downtime deployments and deployment frequency went from once a week to 12x per day. Exceptional work.",
    rating: 5,
    category: "devops",
  },
  {
    name: "Priya Nair",
    role: "CISO",
    company: "Healthcare SaaS, Hyderabad",
    avatar: "PN",
    content: "Their security team identified 4 critical vulnerabilities in our infrastructure that our previous vendor missed. The remediation playbook they provided was world-class.",
    rating: 5,
    category: "security",
  },
  {
    name: "Ravi Shankar",
    role: "SAP Program Manager",
    company: "Manufacturing Enterprise, Pune",
    avatar: "RS",
    content: "Our SAP SD migration was stalled for 6 months. VAREX came in, restructured the delivery plan, and we went live in 8 weeks. They know SAP inside out.",
    rating: 5,
    category: "sap",
  },
  {
    name: "Sneha Kulkarni",
    role: "Head of Talent",
    company: "D2C Brand, Mumbai",
    avatar: "SK",
    content: "The AI-assisted hiring framework reduced our time-to-hire for DevOps roles from 11 weeks to 3. The interview templates alone are worth the subscription.",
    rating: 5,
    category: "hiring",
  },
  {
    name: "Karthik Reddy",
    role: "Cloud Architect",
    company: "EdTech Scale-up, Chennai",
    avatar: "KR",
    content: "Attended the Kubernetes & DevSecOps workshop. The hands-on labs were production-grade scenarios, not toy examples. Immediately applied everything the next day.",
    rating: 5,
    category: "workshop",
  },
  {
    name: "Ananya Iyer",
    role: "Backend Engineer",
    company: "Series B Startup, Bengaluru",
    avatar: "AI",
    content: "The premium learning modules on architecture reviews changed how I approach system design. Got an offer from a FAANG-adjacent company 2 months after subscribing.",
    rating: 5,
    category: "devops",
  },
];

const CATEGORY_FILTERS = [
  { key: "all", label: "All" },
  { key: "devops", label: "DevOps" },
  { key: "security", label: "Security" },
  { key: "sap", label: "SAP SD" },
  { key: "hiring", label: "AI Hiring" },
  { key: "workshop", label: "Workshops" },
] as const;

function Stars({ n }: { n: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg key={i} viewBox="0 0 20 20" fill={i < n ? "#f59e0b" : "#334155"} className="h-4 w-4">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

export default function Testimonials() {
  const [filter, setFilter] = useState<string>("all");

  const shown = filter === "all"
    ? TESTIMONIALS
    : TESTIMONIALS.filter((t) => t.category === filter);

  return (
    <section className="space-y-10">
      <AnimateIn className="text-center space-y-3">
        <h2 className="text-sm font-bold tracking-widest text-sky-400 uppercase">
          Client Stories
        </h2>
        <h3 className="text-3xl md:text-4xl font-extrabold text-white">
          Trusted by Engineering Teams Across India
        </h3>
        <p className="text-base text-slate-400 max-w-lg mx-auto">
          From early-stage startups to large enterprises — hear what our clients have to say.
        </p>
      </AnimateIn>

      {/* Category filter pills */}
      <AnimateIn delay={0.1} className="flex flex-wrap justify-center gap-2">
        {CATEGORY_FILTERS.map((f) => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-all duration-300 ${filter === f.key
                ? "bg-sky-500 text-white shadow-lg shadow-sky-500/25"
                : "bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white"
              }`}>
            {f.label}
          </button>
        ))}
      </AnimateIn>

      {/* Testimonial cards */}
      <StaggerContainer className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" staggerDelay={0.07}>
        {shown.map((t) => (
          <StaggerItem key={t.name}>
            <div className="h-full rounded-2xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/60 p-6 space-y-4 flex flex-col transition-all duration-300 hover:border-sky-500/30 hover:-translate-y-1 hover:shadow-xl hover:shadow-sky-900/10">
              <Stars n={t.rating} />
              <p className="text-sm text-slate-200 leading-relaxed flex-1">
                &ldquo;{t.content}&rdquo;
              </p>
              <div className="flex items-center gap-3 pt-3 border-t border-slate-800">
                <div className="flex h-10 w-10 items-center justify-center rounded-full
                  bg-gradient-to-br from-sky-500/20 to-indigo-500/20 text-sky-300 text-sm font-bold flex-shrink-0 border border-sky-500/20">
                  {t.avatar}
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{t.name}</p>
                  <p className="text-xs text-slate-400">{t.role} · {t.company}</p>
                </div>
              </div>
            </div>
          </StaggerItem>
        ))}
      </StaggerContainer>

      {/* Summary bar */}
      <AnimateIn>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40
          grid grid-cols-3 divide-x divide-slate-800 text-center p-6">
          {[
            { value: "50+", label: "Clients served" },
            { value: "4.9★", label: "Average rating" },
            { value: "100%", label: "Would recommend" },
          ].map((s) => (
            <div key={s.label} className="px-4">
              <p className="text-2xl font-extrabold text-sky-400">{s.value}</p>
              <p className="text-xs text-slate-400 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </AnimateIn>
    </section>
  );
}
