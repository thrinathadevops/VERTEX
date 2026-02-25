// PATH: app/privacy/page.tsx
import { PAGE_META } from "@/lib/metadata";
export const metadata = PAGE_META.privacy;

export default function PrivacyPage() {
  return (
    <article className="max-w-3xl mx-auto space-y-8 prose prose-invert prose-sm">
      <header className="not-prose space-y-2">
        <h1 className="text-2xl font-bold">Privacy Policy</h1>
        <p className="text-xs text-slate-400">Last updated: 1 January 2025</p>
      </header>

      {[
        {
          title: "1. Who we are",
          body: "VAREX Technologies (\"VAREX\", \"we\", \"our\") is a technology consulting and SaaS company headquartered in Bengaluru, Karnataka, India. This policy explains how we collect, use, and protect your data when you use varextech.in.",
        },
        {
          title: "2. What we collect",
          body: "We collect: (a) Account data — name, email, hashed password, and role when you register. (b) Payment data — Razorpay order IDs and payment IDs; we never store raw card or UPI details. (c) Usage data — pages visited, workshop registrations, content accessed. (d) Communication data — messages submitted through the contact/consultation form.",
        },
        {
          title: "3. How we use your data",
          body: "We use your data to: provide and improve the VAREX platform; process subscription payments via Razorpay; send transactional emails (registration, payment receipts, workshop reminders) via SendGrid; respond to consultation requests; and comply with applicable Indian laws including the IT Act 2000.",
        },
        {
          title: "4. Data sharing",
          body: "We do not sell your personal data. We share data only with: Razorpay (payment processing), AWS S3 (file storage), SendGrid (email delivery). All processors are contractually bound to GDPR/PDPA-equivalent obligations.",
        },
        {
          title: "5. Cookies",
          body: "We use strictly necessary cookies (auth session token) and optional analytics cookies. You can withdraw consent for optional cookies at any time via the cookie banner.",
        },
        {
          title: "6. Data retention",
          body: "Account data is retained for the duration of your account plus 2 years. Payment records are retained for 7 years as required by Indian GST law. You may request deletion of non-financial data by emailing privacy@varextech.in.",
        },
        {
          title: "7. Your rights",
          body: "You have the right to: access, correct, or delete your personal data; withdraw marketing consent at any time; lodge a complaint with the relevant data protection authority. Email privacy@varextech.in for any requests.",
        },
        {
          title: "8. Security",
          body: "Passwords are bcrypt-hashed. Data in transit is encrypted via TLS 1.2+. S3 buckets are private by default; files are accessible only via signed URLs. We conduct regular security reviews.",
        },
        {
          title: "9. Changes",
          body: "We may update this policy. Material changes will be notified via email or a banner on the site. Continued use after 30 days constitutes acceptance.",
        },
        {
          title: "10. Contact",
          body: "VAREX Technologies · Bengaluru, Karnataka · privacy@varextech.in",
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
