import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    try {
        const signature = req.headers.get("x-razorpay-signature");
        if (!signature) {
            return NextResponse.json({ detail: "Missing signature" }, { status: 400 });
        }

        const bodyText = await req.text();

        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/webhooks/razorpay`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-razorpay-signature": signature,
                },
                body: bodyText,
            }
        );

        if (!res.ok) {
            const errorData = await res.text();
            console.error("Webhook processing failed on backend:", errorData);
            return NextResponse.json({ detail: "Webhook failed" }, { status: res.status });
        }

        return NextResponse.json({ success: true });
    } catch (err) {
        console.error("Webhook route error:", err);
        return NextResponse.json({ detail: "Internal Server Error" }, { status: 500 });
    }
}
