// PATH: app/services/[slug]/page.tsx
import { notFound } from "next/navigation";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";

const SERVICES: Record<string, {
  title: string; icon: string; tagline: string; description: string;
  offerings: string[]; outcomes: string[]; techStack: string[];
}> = {
  devsecops: {
    title: "DevSecOps",
    icon: "⚙️",
    tagline: "Secure by design, fast by default.",
    description: "We embed security into your CI/CD pipelines, migrate workloads to Kubernetes, and implement GitOps-driven delivery. From zero to production-grade infrastructure in weeks, not months.",
    offerings: [
      "CI/CD pipeline design & implementation (GitHub Actions, GitLab CI, ArgoCD)",
      "Kubernetes cluster setup, hardening & cost optimisation",
      "Infrastructure as Code (Terraform, Pulumi, Ansible)",
      "SRE: SLI/SLO definition, alerting, runbooks",
      "Container security scanning (Trivy, Snyk)",
      "Secrets management (HashiCorp Vault, AWS Secrets Manager)",
    ],
    outcomes: [
      "Deployment frequency 10x higher",
      "Mean time to recovery under 15 minutes",
      "Zero-downtime release pipelines",
      "SOC 2 / ISO 27001-ready infrastructure",
    ],
    techStack: ["Kubernetes", "GitHub Actions", "ArgoCD", "Terraform", "Prometheus", "Grafana", "Vault"],
  },
  cybersecurity: {
    title: "Cybersecurity",
    icon: "🛡",
    tagline: "Find it before attackers do.",
    description: "Our certified security engineers conduct penetration tests, architect zero-trust networks, and build compliance programmes for fintech, healthtech, and SaaS companies.",
    offerings: [
      "Web & API penetration testing (OWASP Top 10)",
      "Cloud security posture management (AWS/GCP/Azure)",
      "Zero-trust network architecture design",
      "Threat modelling & attack surface analysis",
      "ISO 27001 / SOC 2 readiness assessments",
      "Security awareness training for engineering teams",
    ],
    outcomes: [
      "Critical vulnerabilities identified before production",
      "Compliance readiness in 8–12 weeks",
      "Reduced attack surface by 60%+",
      "Board-ready security posture reports",
    ],
    techStack: ["Burp Suite", "Nessus", "AWS Security Hub", "OWASP ZAP", "Falco", "Wazuh"],
  },
  "sap-sd": {
    title: "SAP SD",
    icon: "📦",
    tagline: "SAP delivery without the delays.",
    description: "VAREX SAP SD consultants have delivered 30+ order-to-cash implementations across manufacturing, FMCG, and pharma. We specialise in complex integrations, migration rescues, and billing optimisation.",
    offerings: [
      "SAP SD configuration: sales orders, delivery, billing",
      "Pricing procedure design & condition technique",
      "S/4HANA migration planning & execution",
      "Integration with MM, FI/CO, WM modules",
      "Output management: e-invoicing, GST compliance",
      "Support & optimisation of existing SD landscapes",
    ],
    outcomes: [
      "Order-to-cash cycle reduced by 30%",
      "100% GST-compliant billing outputs",
      "On-time, on-budget SAP go-lives",
      "Zero business disruption during migration",
    ],
    techStack: ["SAP S/4HANA", "SAP ECC 6.0", "ABAP", "SAP BTP", "IDOC", "RFC"],
  },
  "ai-hiring": {
    title: "AI Hiring",
    icon: "🤖",
    tagline: "Hire the right engineer in 7 days.",
    description: "We combine AI screening, structured competency interviews, and our pre-vetted talent pool to help you hire DevSecOps, SAP SD, and cloud engineers faster than any traditional recruiter.",
    offerings: [
      "AI-powered resume screening & skills matching",
      "Structured technical interview design",
      "Pre-vetted candidate shortlisting within 48 hours",
      "Interview-to-offer playbooks for hiring managers",
      "90-day retention guarantee",
      "Employer branding advisory for engineering roles",
    ],
    outcomes: [
      "Time-to-hire reduced from 11 weeks to 7 days",
      "90%+ offer acceptance rate",
      "60% lower cost-per-hire vs traditional agencies",
      "Pre-vetted candidates — zero wasted interview slots",
    ],
    techStack: ["Proprietary AI screening", "Structured interviews", "Skills graph matching"],
  },
};

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const s = SERVICES[params.slug];
  if (!s) return {};
  return buildMetadata({
    title:       `${s.title} Consulting`,
    description: s.tagline + " " + s.description.slice(0, 100),
    path:        `/services/${params.slug}`,
  });
}

export async function generateStaticParams() {
  return Object.keys(SERVICES).map((slug) => ({ slug }));
}

export default function ServiceDetailPage({ params }: { params: { slug: string } }) {
  const service = SERVICES[params.slug];
  if (!service) notFound();

  return (
    <div className="max-w-4xl mx-auto space-y-8">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/services" className="hover:text-sky-300">Services</Link>
        <span>/</span>
        <span className="text-slate-300">{service.title}</span>
      </nav>

      {/* Header */}
      <header className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{service.icon}</span>
          <h1 className="text-3xl font-bold">{service.title}</h1>
        </div>
        <p className="text-lg text-sky-300 font-medium">{service.tagline}</p>
        <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">{service.description}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* What we offer */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-slate-100">What we deliver</h2>
          <ul className="space-y-2">
            {service.offerings.map((o) => (
              <li key={o} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="text-sky-400 mt-0.5 flex-shrink-0">→</span>{o}
              </li>
            ))}
          </ul>
        </section>

        {/* Outcomes */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-slate-100">Outcomes you can expect</h2>
          <ul className="space-y-2">
            {service.outcomes.map((o) => (
              <li key={o} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="text-emerald-400 mt-0.5 flex-shrink-0">✓</span>{o}
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* Tech stack */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-100">Tools & technologies</h2>
        <div className="flex flex-wrap gap-2">
          {service.techStack.map((t) => (
            <span key={t}
              className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300">
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="rounded-2xl border border-sky-800/40 bg-sky-950/20 p-6
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-sky-100">
            Ready to get started with {service.title}?
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Book a free 30-minute discovery call with one of our specialists.
          </p>
        </div>
        <Link href={`/contact?service=${params.slug}`}
          className="flex-shrink-0 rounded-md bg-sky-500 px-5 py-2.5 text-xs font-semibold
            text-white hover:bg-sky-400 transition">
          Book free consultation
        </Link>
      </div>

    </div>
  );
}
