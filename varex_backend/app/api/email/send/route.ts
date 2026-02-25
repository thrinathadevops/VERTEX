// PATH: app/api/email/send/route.ts
import { NextRequest, NextResponse } from "next/server";
import { sendEmail, type EmailTemplate } from "@/lib/email";

export async function POST(req: NextRequest) {
  const secret = req.headers.get("x-internal-secret");
  if (secret !== process.env.INTERNAL_API_SECRET) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { to, name, template, data } = await req.json() as {
    to: string;
    name: string;
    template: EmailTemplate;
    data?: Record<string, string>;
  };

  try {
    await sendEmail({ to, name, template, data });
    return NextResponse.json({ sent: true });
  } catch (err: any) {
    console.error("Email send error:", err.message);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
