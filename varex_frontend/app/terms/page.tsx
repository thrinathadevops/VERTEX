// PATH: app/terms/page.tsx
import { PAGE_META } from "@/lib/metadata";
export const metadata = PAGE_META.terms;

export default function TermsPage() {
  return (
    <article className="max-w-3xl mx-auto space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">Terms of Service</h1>
        <p className="text-xs text-slate-400">Last updated: 1 January 2025</p>
      </header>

      {[
        {
          title: "1. Acceptance",
          body: "By accessing or using varextech.in you agree to these Terms. If you do not agree, please do not use the platform.",
        },
        {
          title: "2. Services",
          body: "VAREX provides DevSecOps consulting, cybersecurity advisory, SAP SD delivery, AI-powered hiring frameworks, premium learning content, and workshop delivery. Service scope is defined in individual statements of work or subscription plans.",
        },
        {
          title: "3. Accounts",
          body: "You must provide accurate information when registering. You are responsible for all activity under your account. Do not share credentials. VAREX reserves the right to suspend accounts that violate these Terms.",
        },
        {
          title: "4. Subscriptions & Payments",
          body: "Subscriptions are billed monthly or quarterly in INR via Razorpay. Prices are displayed inclusive of applicable taxes. Subscriptions auto-renew unless cancelled before the renewal date. Enterprise plans are governed by separate contracts.",
        },
        {
          title: "5. Intellectual Property",
          body: "All platform content — articles, templates, architecture diagrams, course modules — is owned by VAREX Technologies or its licensors. You may not reproduce, redistribute, or resell content without written permission.",
        },
        {
          title: "6. Acceptable Use",
          body: "You may not: use the platform for unlawful purposes; attempt to reverse-engineer or scrape the platform; share premium credentials with non-subscribers; upload malicious content; or impersonate VAREX staff.",
        },
        {
          title: "7. Limitation of Liability",
          body: "To the maximum extent permitted by Indian law, VAREX shall not be liable for indirect, incidental, or consequential damages. Our total liability is limited to the amount you paid in the 3 months preceding the claim.",
        },
        {
          title: "8. Governing Law",
          body: "These Terms are governed by the laws of India. Disputes shall be subject to the exclusive jurisdiction of courts in Bengaluru, Karnataka.",
        },
        {
          title: "9. Changes",
          body: "We may update these Terms with 30 days notice. Continued use constitutes acceptance.",
        },
        {
          title: "10. Contact",
          body: "legal@varextech.in · VAREX Technologies · Bengaluru, Karnataka, India",
        },
      ].map((section) => (
        <section key={section.title} className="space-y-2">
          <h2 className="text-base font-semibold text-slate-100">{section.title}</h2>
          <p className="text-sm text-slate-300 leading-relaxed">{section.body}</p>
        </section>
      ))}
    </article>
  );
}
