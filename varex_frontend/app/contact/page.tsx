"use client";
import { useState } from "react";
import { submitLead } from "@/lib/api";

const SERVICES = [
  { value: "devsecops",     label: "DevSecOps Implementation" },
  { value: "cybersecurity", label: "Cybersecurity & Audit" },
  { value: "sap_sd",        label: "SAP SD Consulting" },
  { value: "ai_hiring",     label: "AI-Powered Hiring" },
  { value: "consulting",    label: "General Consulting" },
  { value: "training",      label: "Corporate Training" },
  { value: "workshop",      label: "Workshop Registration" },
  { value: "other",         label: "Other" },
];

export default function ContactPage() {
  const [form, setForm] = useState({
    name: "", email: "", phone: "", company: "",
    service_interest: "consulting", message: "", preferred_slot: "",
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      await submitLead(form);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message ?? "Submission failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) return (
    <div className="max-w-md mx-auto rounded-2xl border border-emerald-700/50 bg-emerald-950/40 p-6 text-center">
      <p className="text-2xl mb-2">✅</p>
      <h2 className="text-base font-semibold text-emerald-200">Thank you!</h2>
      <p className="text-sm text-emerald-100/80 mt-1">We'll reach out within 24 hours.</p>
    </div>
  );

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold mb-1">Contact & Free Consultation</h1>
        <p className="text-sm text-slate-300">Book a free 30-min consultation or reach out for any service enquiry.</p>
      </header>
      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 space-y-4">
        {[
          { name: "name", label: "Full name", type: "text", required: true },
          { name: "email", label: "Email", type: "email", required: true },
          { name: "phone", label: "Phone (optional)", type: "tel", required: false },
          { name: "company", label: "Company (optional)", type: "text", required: false },
          { name: "preferred_slot", label: "Preferred slot (e.g. Mon 10am IST)", type: "text", required: false },
        ].map(({ name, label, type, required }) => (
          <div key={name}>
            <label className="mb-1 block text-xs font-medium text-slate-200">{label}</label>
            <input name={name} type={type} required={required} value={(form as any)[name]}
              onChange={handleChange}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500" />
          </div>
        ))}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-200">Service interested in</label>
          <select name="service_interest" value={form.service_interest} onChange={handleChange}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500">
            {SERVICES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-200">Message</label>
          <textarea name="message" rows={4} value={form.message} onChange={handleChange}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500 resize-none" />
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full rounded-md bg-sky-500 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-400 disabled:opacity-60">
          {loading ? "Sending..." : "Book Free Consultation"}
        </button>
      </form>
    </div>
  );
}
