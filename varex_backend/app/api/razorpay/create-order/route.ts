// PATH: app/api/razorpay/create-order/route.ts
import { NextRequest, NextResponse } from "next/server";
import Razorpay from "razorpay";
import { cookies } from "next/headers";

const PLAN_PRICES: Record<string, number> = {
  monthly:   149900,
  quarterly: 399900,
};

const rzp = new Razorpay({
  key_id:     process.env.RAZORPAY_KEY_ID     ?? "",
  key_secret: process.env.RAZORPAY_KEY_SECRET ?? "",
});

export async function POST(req: NextRequest) {
  try {
    const { plan_type } = await req.json();
    const amount = PLAN_PRICES[plan_type];
    if (amount === undefined) {
      return NextResponse.json({ error: "Invalid plan type" }, { status: 400 });
    }

    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value ?? "";

    // Create pending subscription record in DB
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/subscriptions`, {
      method:  "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body:    JSON.stringify({ plan_type, status: "pending" }),
    });

    const order = await rzp.orders.create({
      amount,
      currency: "INR",
      receipt:  `varex_${plan_type}_${Date.now()}`,
    });

    return NextResponse.json(order);
  } catch (err) {
    console.error("create-order error:", err);
    return NextResponse.json({ error: "Order creation failed" }, { status: 500 });
  }
}
