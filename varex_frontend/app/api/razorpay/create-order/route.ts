// PATH: varex_frontend/app/api/razorpay/create-order/route.ts
// FIX: Bug 4.1 — This route was called by lib/razorpay.ts but didn't exist

import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const token = req.cookies.get("access_token")?.value;

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/subscriptions`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      }
    );

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ detail: "Failed to create order" }, { status: 500 });
  }
}
