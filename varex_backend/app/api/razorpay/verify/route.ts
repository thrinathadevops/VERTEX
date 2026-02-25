// PATH: app/api/razorpay/verify/route.ts
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { cookies } from "next/headers";

export async function POST(req: NextRequest) {
  try {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = await req.json();

    const body     = `${razorpay_order_id}|${razorpay_payment_id}`;
    const expected = crypto
      .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET ?? "")
      .update(body)
      .digest("hex");

    if (expected !== razorpay_signature) {
      return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
    }

    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value ?? "";

    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/subscriptions/activate`, {
      method:  "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body:    JSON.stringify({ razorpay_order_id, razorpay_payment_id }),
    });

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("verify error:", err);
    return NextResponse.json({ error: "Verification failed" }, { status: 500 });
  }
}
