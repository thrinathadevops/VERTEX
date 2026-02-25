// PATH: app/refund/page.tsx
import Link from "next/link";
import { PAGE_META } from "@/lib/metadata";
export const metadata = PAGE_META.refund;

export default function RefundPage() {
  return (
    <article className="max-w-3xl mx-auto space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">Refund & Cancellation Policy</h1>
        <p className="text-xs text-slate-400">Last updated: 1 January 2025 · Razorpay-compliant</p>
      </header>

      {[
        {
          title: "1. Subscriptions",
          body: "Monthly and quarterly subscriptions may be cancelled at any time. Cancellation takes effect at the end of the current billing period — you retain access until then. We do not offer pro-rata refunds for partial periods. To cancel, go to Dashboard → Subscription → Cancel.",
        },
        {
          title: "2. Refund eligibility",
          body: "You are eligible for a full refund if: (a) you request within 7 days of first payment and have not accessed more than 3 premium modules, or (b) you were double-charged due to a technical error. Refund requests must be submitted to support@varextech.in with your Razorpay payment ID.",
        },
        {
          title: "3. Workshops",
          body: "Workshop registrations are refundable in full if cancelled 7+ days before the workshop date. Cancellations within 7 days receive a 50% refund or a credit toward a future workshop. No-shows are not refundable.",
        },
        {
          title: "4. Consulting engagements",
          body: "Consulting retainers are governed by individual statements of work. Generally, work completed prior to cancellation is non-refundable. Unused retainer hours are refunded on a pro-rata basis within 14 business days.",
        },
        {
          title: "5. Processing time",
          body: "Approved refunds are processed within 5–7 business days to the original payment method via Razorpay. Bank processing time may add 3–5 additional business days.",
        },
        {
          title: "6. Non-refundable items",
          body: "One-time purchases (architecture templates, downloadable resources), expired subscriptions, and enterprise contracts are non-refundable unless otherwise agreed in writing.",
        },
        {
          title: "7. Contact",
          body: "support@varextech.in · Response within 24 business hours · VAREX Technologies, Bengaluru",
        },
      ].map((section) => (
        <section key={section.title} className="space-y-2">
          <h2 className="text-base font-semibold text-slate-100">{section.title}</h2>
          <p className="text-sm text-slate-300 leading-relaxed">{section.body}</p>
        </section>
      ))}

      <div className="rounded-2xl border border-sky-800/40 bg-sky-950/20 p-4 flex items-center justify-between gap-4">
        <p className="text-xs text-slate-300">Need help with a refund or cancellation?</p>
        <Link href="/contact"
          className="flex-shrink-0 rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
          Contact support
        </Link>
      </div>
    </article>
  );
}
