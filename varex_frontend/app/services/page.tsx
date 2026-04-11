import Link from "next/link";
import { Bot, Briefcase, Shield, Boxes, ArrowRight } from "lucide-react";

export default function ServicesPage() {
  const divisions = [
    {
      icon: Briefcase,
      title: "Engineering Services",
      href: "/services/engineering-services",
      items: ["Cloud Architecture Design", "DevSecOps Implementation", "Infrastructure Automation", "Security Hardening", "CI/CD Pipeline Setup"],
    },
    {
      icon: Shield,
      title: "Cybersecurity & Resilience",
      href: "/services/cybersecurity-resilience",
      items: ["DevSecOps Pipelines", "Container Security", "Zero Trust Architecture", "Compliance & Audit (ISO 27001, SOC2)", "VAPT & Threat Modelling"],
    },
    {
      icon: Boxes,
      title: "SAP SD Consulting",
      href: "/services/sap-sd-consulting",
      items: ["S/4HANA SD Module Implementation", "Order-to-Cash Optimisation", "SAP SD Integration (CRM/MM)", "SAP Support & Rollouts", "Pricing & Condition Configuration"],
    },
    {
      icon: Bot,
      title: "AI-Powered Interview Platform",
      href: "/services/ai-powered-interview",

      items: ["Mock Interview — Candidates practice with AI interviewer & get instant feedback", "AI Interview for Clients — Enterprise-grade automated technical assessments", "7-phase adaptive questioning (ice-breaker to deep-dive)", "Multi-criteria AI scoring with detailed evaluation reports", "Resume-aware contextual question generation", "Anti-cheat proctoring & integrity monitoring"],
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 pt-24 pb-16 space-y-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold mb-2">What We Do</h1>
        <p className="text-slate-300 max-w-xl mx-auto text-sm">
          Four specialised divisions delivering engineering, security, SAP consulting, and AI-powered interview solutions.
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-2">
        {divisions.map((div) => (
          <Link href={div.href} key={div.title} className="group flex flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-6 hover:bg-white/[0.05] hover:border-emerald-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl cursor-pointer">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-sky-500/10 text-sky-300 group-hover:scale-110 transition-transform duration-300">
              <div.icon className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold mb-4 group-hover:text-emerald-300 transition-colors">{div.title}</h2>
            <ul className="space-y-2 mb-6 flex-grow">
              {div.items.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-sky-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <span className="inline-flex items-center text-sm font-semibold text-emerald-400 opacity-80 group-hover:opacity-100 transition-all duration-300 mt-auto">
              View Detailed Offering <ArrowRight className="w-4 h-4 ml-1.5 group-hover:translate-x-1.5 transition-transform" />
            </span>
          </Link>
        ))}
      </section>
    </div>
  );
}
