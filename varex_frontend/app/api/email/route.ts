import { NextRequest, NextResponse } from "next/server";
import { sendEmail, EmailTemplate } from "@/lib/email";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { to, name, template, data } = body as {
      to: string;
      name: string;
      template: EmailTemplate;
      data?: Record<string, string | number>;
    };

    if (!to || !name || !template) {
      return NextResponse.json(
        { detail: "Missing to, name, or template fields." },
        { status: 400 }
      );
    }

    await sendEmail({ to, name, template, data });
    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.message || "Failed to send email" },
      { status: 500 }
    );
  }
}
