// PATH: varex_frontend/app/api/razorpay/verify/route.ts

import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature, subscription_id } =
      await req.json();

    // Verify HMAC signature on server (never on client)
    const body       = razorpay_order_id + "|" + razorpay_payment_id;
    const secret     = process.env.RAZORPAY_KEY_SECRET!;
    const expected   = crypto.createHmac("sha256", secret).update(body).digest("hex");

    if (expected !== razorpay_signature) {
      return NextResponse.json({ detail: "Invalid payment signature" }, { status: 400 });
    }

    // Activate subscription in FastAPI backend
    const token = req.cookies.get("access_token")?.value;
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/subscriptions/activate`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ subscription_id, razorpay_payment_id }),
      }
    );

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json({ success: true, ...data });
  } catch {
    return NextResponse.json({ detail: "Verification failed" }, { status: 500 });
  }
}
