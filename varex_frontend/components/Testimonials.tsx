"use client";

import { useState } from "react";

interface Testimonial {
  name:       string;
  role:       string;
  company:    string;
  avatar:     string;
  content:    string;
  rating:     number;
  category:   "devops" | "security" | "sap" | "hiring" | "workshop";
}

const TESTIMONIALS: Testimonial[] = [
  {
    name:     "Arjun Mehta",
    role:     "VP Engineering",
    company:  "FinTech Startup, Bengaluru",
    avatar:   "AM",
    content:  "VAREX rebuilt our entire CI/CD pipeline in 3 weeks. Zero downtime deployments and deployment frequency went from once a week to 12x per day. Exceptional work.",
    rating:   5,
    category: "devops",
  },
  {
    name:     "Priya Nair",
    role:     "CISO",
    company:  "Healthcare SaaS, Hyderabad",
    avatar:   "PN",
    content:  "Their security team identified 4 critical vulnerabilities in our infrastructure that our previous vendor missed. The remediation playbook they provided was world-class.",
    rating:   5,
    category: "security",
  },
  {
    name:     "Ravi Shankar",
    role:     "SAP Program Manager",
    company:  "Manufacturing Enterprise, Pune",
    avatar:   "RS",
    content:  "Our SAP SD migration was stalled for 6 months. VAREX came in, restructured the delivery plan, and we went live in 8 weeks. They know SAP inside out.",
    rating:   5,
    category: "sap",
  },
  {
    name:     "Sneha Kulkarni",
    role:     "Head of Talent",
    company:  "D2C Brand, Mumbai",
    avatar:   "SK",
    content:  "The AI-assisted hiring framework reduced our time-to-hire for DevOps roles from 11 weeks to 3. The interview templates alone are worth the subscription.",
    rating:   5,
    category: "hiring",
  },
  {
    name:     "Karthik Reddy",
    role:     "Cloud Architect",
    company:  "EdTech Scale-up, Chennai",
    avatar:   "KR",
    content:  "Attended the Kubernetes & DevSecOps workshop. The hands-on labs were production-grade scenarios, not toy examples. Immediately applied everything the next day.",
    rating:   5,
    category: "workshop",
  },
  {
    name:     "Ananya Iyer",
    role:     "Backend Engineer",
    company:  "Series B Startup, Bengaluru",
    avatar:   "AI",
    content:  "The premium learning modules on architecture reviews changed how I approach system design. Got an offer from a FAANG-adjacent company 2 months after subscribing.",
    rating:   5,
    category: "devops",
  },
];

const CATEGORY_FILTERS = [
  { key: "all",      label: "All"          },
  { key: "devops",   label: "DevOps"       },
  { key: "security", label: "Security"     },
  { key: "sap",      label: "SAP SD"       },
  { key: "hiring",   label: "AI Hiring"    },
  { key: "workshop", label: "Workshops"    },
] as const;

function Stars({ n }: { n: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg key={i} viewBox="0 0 20 20" fill={i < n ? "#f59e0b" : "#334155"}
          className="h-3 w-3">
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
    <section className="space-y-6">
      <div className="text-center space-y-2">
        <p className="text-xs font-semibold uppercase tracking-widest text-sky-400">
          Client Stories
        </p>
        <h2 className="text-2xl font-bold">Trusted by engineering teams across India</h2>
        <p className="text-sm text-slate-400 max-w-lg mx-auto">
          From early-stage startups to large enterprises — here is what our clients say.
        </p>
      </div>

      {/* Category filter pills */}
      <div className="flex flex-wrap justify-center gap-2">
        {CATEGORY_FILTERS.map((f) => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              filter === f.key
                ? "bg-sky-500 text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Testimonial cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((t) => (
          <div key={t.name}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3 flex flex-col">
            <Stars n={t.rating} />
            <p className="text-sm text-slate-200 leading-relaxed flex-1">
              &ldquo;{t.content}&rdquo;
            </p>
            <div className="flex items-center gap-3 pt-2 border-t border-slate-800">
              <div className="flex h-8 w-8 items-center justify-center rounded-full
                bg-sky-500/20 text-sky-300 text-xs font-bold flex-shrink-0">
                {t.avatar}
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-100">{t.name}</p>
                <p className="text-[11px] text-slate-400">{t.role} · {t.company}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4
        grid grid-cols-3 divide-x divide-slate-800 text-center">
        {[
          { value: "50+",  label: "Clients served"    },
          { value: "4.9★", label: "Average rating"    },
          { value: "100%", label: "Would recommend"   },
        ].map((s) => (
          <div key={s.label} className="px-4">
            <p className="text-xl font-bold text-sky-300">{s.value}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
