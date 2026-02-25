// PATH: app/api/webhook/razorpay/route.ts
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const rawBody   = await req.text();
    const signature = req.headers.get("x-razorpay-signature") ?? "";
    const secret    = process.env.RAZORPAY_WEBHOOK_SECRET ?? "";

    const expected = crypto
      .createHmac("sha256", secret)
      .update(rawBody)
      .digest("hex");

    if (expected !== signature) {
      return NextResponse.json({ error: "Invalid webhook signature" }, { status: 400 });
    }

    const event = JSON.parse(rawBody);

    // Forward to FastAPI for DB processing
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/webhooks/razorpay`, {
      method:  "POST",
      headers: { "Content-Type": "application/json", "x-webhook-secret": secret },
      body:    rawBody,
    });

    console.log("Razorpay webhook received:", event.event);
    return NextResponse.json({ received: true });
  } catch (err) {
    console.error("Webhook error:", err);
    return NextResponse.json({ error: "Webhook processing failed" }, { status: 500 });
  }
}
