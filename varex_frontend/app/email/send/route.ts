// PATH: varex_frontend/app/api/email/send/route.ts
// FIX: Bug 4.3 — SENDGRID_API_KEY moved server-side only (no longer exposed to browser)

import { NextRequest, NextResponse } from "next/server";

const SENDGRID_API = "https://api.sendgrid.com/v3/mail/send";
const FROM_EMAIL   = "noreply@varextech.in";
const FROM_NAME    = "VAREX Technologies";

// Validate internal requests (from Next.js server only)
function isAuthorized(req: NextRequest): boolean {
  const secret = req.headers.get("x-internal-secret");
  return secret === process.env.INTERNAL_API_SECRET;
}

export async function POST(req: NextRequest) {
  if (!isAuthorized(req)) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  try {
    const { to, subject, html, text } = await req.json();

    if (!to || !subject || (!html && !text)) {
      return NextResponse.json({ detail: "Missing required fields: to, subject, html/text" }, { status: 400 });
    }

    const payload = {
      personalizations: [{ to: [{ email: to }] }],
      from:    { email: FROM_EMAIL, name: FROM_NAME },
      subject,
      content: [
        ...(html ? [{ type: "text/html",  value: html  }] : []),
        ...(text ? [{ type: "text/plain", value: text  }] : []),
      ],
    };

    const res = await fetch(SENDGRID_API, {
      method:  "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${process.env.SENDGRID_API_KEY}`,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.text();
      console.error("SendGrid error:", err);
      return NextResponse.json({ detail: "Email send failed" }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Email route error:", err);
    return NextResponse.json({ detail: "Internal error" }, { status: 500 });
  }
}
