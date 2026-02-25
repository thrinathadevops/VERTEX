// lib/email.ts — server-side email sender via SendGrid

export type EmailTemplate =
  | "welcome"
  | "lead_confirmation"
  | "workshop_registration"
  | "subscription_activated"
  | "subscription_expiry_reminder";

export interface SendEmailOptions {
  to:       string;
  name:     string;
  template: EmailTemplate;
  data?:    Record<string, string | number>;
}

const TEMPLATES: Record<EmailTemplate, { subject: string; html: (d: Record<string, string | number>) => string }> = {
  welcome: {
    subject: "Welcome to VAREX 🚀",
    html: (d) => `
      <h2>Welcome, ${d.name}!</h2>
      <p>Your VAREX account is ready. Start exploring our DevSecOps, Security, and SAP SD resources.</p>
      <a href="https://varextech.in/learnings" style="background:#0ea5e9;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
        Explore Learning Paths
      </a>
      <p style="color:#94a3b8;font-size:12px;margin-top:24px;">VAREX Technologies · Bengaluru, India</p>
    `,
  },
  lead_confirmation: {
    subject: "We received your consultation request ✅",
    html: (d) => `
      <h2>Hi ${d.name},</h2>
      <p>Thanks for reaching out! We have received your request for <strong>${d.service}</strong>.</p>
      <p>Our team will contact you within <strong>24 hours</strong>.</p>
      <p>— The VAREX Team</p>
    `,
  },
  workshop_registration: {
    subject: `You're registered: ${"{title}"}`,
    html: (d) => `
      <h2>Registration confirmed 🎓</h2>
      <p>Hi ${d.name}, you are registered for <strong>${d.title}</strong>.</p>
      <p>📅 Date: ${d.date}<br/>📡 Mode: ${d.mode}</p>
      <p>We will send a reminder 24 hours before the session.</p>
    `,
  },
  subscription_activated: {
    subject: "⭐ Your VAREX Premium is active",
    html: (d) => `
      <h2>You are Premium now! ⭐</h2>
      <p>Hi ${d.name}, your <strong>${d.plan}</strong> subscription is active until <strong>${d.expiry}</strong>.</p>
      <a href="https://varextech.in/learnings" style="background:#0ea5e9;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
        Access Premium Content
      </a>
    `,
  },
  subscription_expiry_reminder: {
    subject: "Your VAREX plan expires in 7 days",
    html: (d) => `
      <h2>Plan expiring soon ⏰</h2>
      <p>Hi ${d.name}, your subscription expires on <strong>${d.expiry}</strong>.</p>
      <a href="https://varextech.in/pricing" style="background:#0ea5e9;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
        Renew Now
      </a>
    `,
  },
};

export async function sendEmail({ to, name, template, data = {} }: SendEmailOptions) {
  const t = TEMPLATES[template];
  if (!t) throw new Error(`Unknown email template: ${template}`);

  const payload = {
    personalizations: [{ to: [{ email: to, name }] }],
    from:     { email: "noreply@varextech.in", name: "VAREX Technologies" },
    reply_to: { email: "support@varextech.in" },
    subject:  t.subject.replace("{title}", String(data.title ?? "")),
    content: [{
      type:  "text/html",
      value: t.html({ name, ...data }),
    }],
  };

  const res = await fetch("https://api.sendgrid.com/v3/mail/send", {
    method:  "POST",
    headers: {
      Authorization:  `Bearer ${process.env.SENDGRID_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`SendGrid error: ${err}`);
  }
}
