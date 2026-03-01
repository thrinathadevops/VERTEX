// PATH: app/services/[slug]/page.tsx
import { notFound } from "next/navigation";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import type { ComponentProps } from "react";
import {
  ArrowRightLeft,
  Cloud,
  Package,
  TrendingUp,
  Shield,
  BarChart3,
  Landmark,
  Cog,
  Bot,
  Boxes,
  Check,
  type LucideIcon,
} from "lucide-react";

const SERVICES: Record<string, {
  title: string; icon: string; tagline: string; description: string;
  offerings: string[]; outcomes: string[]; techStack: string[];
}> = {
  "ci-cd-pipeline-setup": {
    title: "CI/CD Pipeline Setup",
    icon: "cicd",
    tagline: "Automate delivery from commit to production.",
    description: "We design robust CI/CD pipelines for faster, safer releases with built-in quality gates, rollback strategy, and environment controls.",
    offerings: [
      "Pipeline architecture for build, test, and release stages",
      "Jenkins and GitHub Actions implementation and hardening",
      "Branch strategy, environment promotion, and release governance",
      "Automated unit, integration, and security test orchestration",
      "Versioning, artifacts, and release traceability setup",
      "Rollback and deployment safety controls for production",
    ],
    outcomes: [
      "Higher release frequency with lower deployment risk",
      "Reduced manual effort across engineering and operations",
      "Repeatable, auditable release process for every team",
      "Faster recovery using standardized rollback workflows",
    ],
    techStack: ["Jenkins", "GitHub Actions", "GitLab CI", "SonarQube", "Nexus", "ArgoCD"],
  },
  "cloud-infrastructure-automation": {
    title: "Cloud Infrastructure Setup & Automation",
    icon: "cloud",
    tagline: "Provision secure, scalable cloud foundations.",
    description: "We build cloud-ready landing zones and automate infrastructure across AWS, Azure, and GCP with IaC best practices.",
    offerings: [
      "Cloud landing zone design for multi-account and multi-env setups",
      "Terraform modules and reusable infrastructure blueprints",
      "Network, IAM, encryption, and secret management setup",
      "Automated provisioning for compute, storage, and databases",
      "Policy enforcement for governance, cost, and compliance",
      "Backup, disaster recovery, and availability architecture",
    ],
    outcomes: [
      "Faster infrastructure provisioning with consistent standards",
      "Improved security posture across cloud environments",
      "Lower operational drift and fewer manual misconfigurations",
      "Better cost control with environment-level governance",
    ],
    techStack: ["AWS", "Azure", "GCP", "Terraform", "Terragrunt", "Ansible", "CloudWatch"],
  },
  "containerization-orchestration": {
    title: "Containerization & Orchestration",
    icon: "container",
    tagline: "Run applications reliably at scale.",
    description: "We containerize workloads and build Kubernetes platforms optimized for high availability, performance, and operational simplicity.",
    offerings: [
      "Application containerization with Docker best practices",
      "Kubernetes cluster setup for dev, staging, and production",
      "Ingress, service mesh, and internal networking configuration",
      "Helm-based deployment packaging and versioning",
      "Horizontal and vertical autoscaling strategies",
      "Cluster security hardening and runtime policy controls",
    ],
    outcomes: [
      "Portable and repeatable deployments across environments",
      "Higher platform reliability under changing workloads",
      "Reduced deployment errors via standardized packaging",
      "Improved resource utilization and platform efficiency",
    ],
    techStack: ["Docker", "Kubernetes", "Helm", "NGINX Ingress", "Istio", "KEDA"],
  },
  "monitoring-logging-solutions": {
    title: "Monitoring & Logging Solutions",
    icon: "monitoring",
    tagline: "Observe, alert, and resolve faster.",
    description: "We implement real-time observability stacks to detect issues early, reduce downtime, and improve incident response maturity.",
    offerings: [
      "Metrics instrumentation and service-level monitoring",
      "Prometheus and Grafana dashboard architecture",
      "Centralized log aggregation and retention strategy",
      "Loki-based log querying and incident correlation",
      "Alert routing, on-call policies, and escalation paths",
      "SLO, error budget, and reliability reporting setup",
    ],
    outcomes: [
      "Lower MTTD and MTTR during incidents",
      "Proactive issue detection before customer impact",
      "Improved operational visibility across services",
      "Actionable reliability insights for engineering teams",
    ],
    techStack: ["Prometheus", "Grafana", "Loki", "Alertmanager", "OpenTelemetry", "ELK"],
  },
  "devsecops-implementation": {
    title: "DevSecOps Implementation",
    icon: "security",
    tagline: "Embed security in every delivery stage.",
    description: "We integrate security scanning, policy enforcement, and compliance controls directly into your software delivery lifecycle.",
    offerings: [
      "SAST, DAST, and dependency scanning in CI/CD pipelines",
      "Container image scanning and admission policy checks",
      "Secrets detection and key leakage prevention workflows",
      "Security gates with risk-based deployment approvals",
      "Compliance mapping for ISO 27001 and SOC 2 controls",
      "Developer security enablement and secure coding practices",
    ],
    outcomes: [
      "Earlier vulnerability detection with reduced rework",
      "Stronger compliance readiness for audits",
      "Secure release cycles without slowing delivery velocity",
      "Measurable reduction in critical security exposures",
    ],
    techStack: ["Trivy", "Snyk", "OWASP ZAP", "Semgrep", "Vault", "OPA"],
  },
  "capacity-planning-optimization": {
    title: "Capacity Planning & Optimization",
    icon: "analytics",
    tagline: "Balance performance, scale, and spend.",
    description: "We optimize cloud, Kubernetes, and on-prem workloads for cost efficiency, throughput, and long-term capacity resilience.",
    offerings: [
      "Resource baselining for cloud, Kubernetes, and on-prem workloads",
      "Demand forecasting and scaling policy design",
      "Workload right-sizing and resource allocation tuning",
      "Node and cluster capacity optimization for Kubernetes",
      "Cost-performance analysis and optimization roadmap",
      "Capacity governance with periodic review cadences",
    ],
    outcomes: [
      "Lower infrastructure spend without service degradation",
      "Fewer capacity bottlenecks during traffic peaks",
      "Improved SLA adherence under variable demand",
      "Data-driven planning for growth and reliability",
    ],
    techStack: ["Kubernetes", "Prometheus", "Grafana", "AWS Cost Explorer", "Azure Monitor", "FinOps tooling"],
  },
  "finops-cost-governance": {
    title: "FinOps & Cost Governance",
    icon: "finops",
    tagline: "Control cloud spend without slowing delivery.",
    description: "We establish FinOps operating models that give engineering and finance shared visibility into cloud costs, budgets, and optimization actions.",
    offerings: [
      "Cloud cost baseline, tagging strategy, and ownership mapping",
      "Budget guardrails and spend anomaly alerting workflows",
      "Service-level cost allocation and unit economics visibility",
      "Rightsizing, reserved capacity, and commitment planning",
      "Cost governance policies aligned with delivery teams",
      "Monthly optimization reviews with actionable execution plans",
    ],
    outcomes: [
      "Improved cost transparency across teams and services",
      "Reduced waste from overprovisioned infrastructure",
      "Predictable cloud budgeting with fewer billing surprises",
      "Higher engineering accountability for cost-performance tradeoffs",
    ],
    techStack: ["AWS Cost Explorer", "Azure Cost Management", "GCP Billing", "Kubernetes", "Prometheus", "Grafana"],
  },
  devsecops: {
    title: "DevSecOps",
    icon: "cog",
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
    icon: "security",
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
    icon: "container",
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
    title: "AI Interview Platform",
    icon: "ai",
    tagline: "AI-powered interviews that scale your hiring.",
    description: "Our AI Interview Platform offers two modes: Mock Interviews for candidates to practice and refine their skills, and AI Interviews for Clients — fully automated enterprise-grade technical assessments with no human interviewer needed.",
    offerings: [
      "Mock Interview — Candidates practice with an AI interviewer and receive instant feedback",
      "AI Interview for Clients — Automated technical assessments for enterprise hiring",
      "7-phase adaptive interview flow: ice-breaker, resume validation, technical deep-dive, scenario-based, behavioral, and closing",
      "Multi-criteria AI scoring across technical accuracy, depth, communication, and problem-solving",
      "Resume-aware contextual question generation tailored to candidate experience",
      "Comprehensive AI-generated assessment reports with hire/reject recommendations",
    ],
    outcomes: [
      "Eliminate interviewer bottlenecks — run unlimited parallel assessments",
      "Consistent, bias-free evaluation across all candidates",
      "Detailed skill-gap analysis with actionable improvement tips",
      "80% reduction in time-to-assess vs traditional interview panels",
    ],
    techStack: ["Proprietary AI screening", "Structured interviews", "Skills graph matching"],
  },
  "sap-solutions": {
    title: "SAP Solutions",
    icon: "sap",
    tagline: "Enterprise SAP execution with business alignment.",
    description: "We provide SAP consulting, implementation support, and integration services to streamline enterprise operations and process continuity.",
    offerings: [
      "SAP landscape assessment and transformation planning",
      "Business process alignment across SD, MM, and FI workflows",
      "Integration strategy with enterprise systems and APIs",
      "Configuration, support, and rollout execution services",
      "Governance, documentation, and adoption enablement",
      "Post-go-live optimization and performance tuning",
    ],
    outcomes: [
      "More reliable and predictable SAP program execution",
      "Better cross-functional process consistency",
      "Reduced operational friction across core business flows",
      "Improved SAP adoption and long-term maintainability",
    ],
    techStack: ["SAP S/4HANA", "SAP ECC", "SAP BTP", "ABAP", "IDOC", "RFC"],
  },
  "ai-powered-hiring": {
    title: "AI-Powered Interview Solutions",
    icon: "ai",
    tagline: "Two interview modes. Zero human bottlenecks.",
    description: "VAREX offers a dual-mode AI Interview Platform: Mock Interviews let candidates practice and improve with real-time AI feedback, while AI Interviews for Clients provide fully automated, enterprise-grade technical assessments at scale.",
    offerings: [
      "Mock Interview mode with AI-generated questions and instant scoring",
      "Client Interview mode for automated enterprise hiring assessments",
      "Configurable difficulty levels: Junior, Mid, Senior, Architect",
      "Anti-cheat proctoring with OS-level process and network monitoring",
      "AI-generated final reports with executive summary and recommendations",
      "Multi-provider AI support: Gemini (free), OpenAI (production), Ollama (offline)",
    ],
    outcomes: [
      "Run hundreds of interviews simultaneously without human interviewers",
      "Standardized evaluation criteria across all candidates",
      "Candidates get actionable feedback to improve technical skills",
      "Clients receive detailed, data-driven hiring recommendations",
    ],
    techStack: ["AI Interview Engine", "Multi-LLM Provider", "Anti-Cheat Proctoring", "Adaptive Question Flow", "AI Scoring Rubrics"],
  },
};

const SERVICE_ICONS: Record<string, LucideIcon> = {
  cicd: ArrowRightLeft,
  cloud: Cloud,
  container: Package,
  monitoring: TrendingUp,
  security: Shield,
  analytics: BarChart3,
  finops: Landmark,
  cog: Cog,
  ai: Bot,
  sap: Boxes,
};

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const s = SERVICES[params.slug];
  if (!s) return {};
  return buildMetadata({
    title: `${s.title} Consulting`,
    description: s.tagline + " " + s.description.slice(0, 100),
    path: `/services/${params.slug}`,
  });
}

export async function generateStaticParams() {
  return Object.keys(SERVICES).map((slug) => ({ slug }));
}

export default function ServiceDetailPage({ params }: { params: { slug: string } }) {
  const service = SERVICES[params.slug];
  if (!service) notFound();
  const ServiceIcon = SERVICE_ICONS[service.icon] ?? BriefcaseFallback;

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
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-sky-500/10 text-sky-300">
            <ServiceIcon className="h-6 w-6" />
          </div>
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
                <Check className="h-3.5 w-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />{o}
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

function BriefcaseFallback(props: ComponentProps<"svg">) {
  return <Boxes {...props} />;
}
