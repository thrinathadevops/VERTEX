// lib/razorpay.ts — client-side Razorpay helpers

export interface RazorpayOrder {
  id: string;
  amount: number;        // in paise
  currency: string;
  receipt: string;
}

export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  prefill?: { name?: string; email?: string; contact?: string };
  theme?: { color?: string };
  handler: (response: RazorpayPaymentResponse) => void;
  modal?: { ondismiss?: () => void };
}

export interface RazorpayPaymentResponse {
  razorpay_order_id:   string;
  razorpay_payment_id: string;
  razorpay_signature:  string;
}

declare global {
  interface Window {
    Razorpay: new (options: RazorpayOptions) => { open(): void };
  }
}

/** Dynamically loads the Razorpay checkout script once */
export function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (document.getElementById("razorpay-script")) { resolve(true); return; }
    const script   = document.createElement("script");
    script.id      = "razorpay-script";
    script.src     = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload  = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

/** Creates a Razorpay order via our backend, opens checkout, verifies payment */
export async function initiatePayment({
  planType,
  user,
  onSuccess,
  onError,
  onDismiss,
}: {
  planType:  string;
  user:      { name: string; email: string };
  onSuccess: (paymentId: string) => void;
  onError:   (msg: string) => void;
  onDismiss?: () => void;
}) {
  // Step 1 — load SDK
  const loaded = await loadRazorpayScript();
  if (!loaded) { onError("Failed to load payment SDK. Check your internet."); return; }

  // Step 2 — create order on backend
  const orderRes = await fetch("/api/razorpay/create-order", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ plan_type: planType }),
  });
  if (!orderRes.ok) { onError("Could not create order. Try again."); return; }
  const order: RazorpayOrder = await orderRes.json();

  // Step 3 — open Razorpay checkout
  const options: RazorpayOptions = {
    key:         process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ?? "",
    amount:      order.amount,
    currency:    order.currency,
    name:        "VAREX Technologies",
    description: `${planType.charAt(0).toUpperCase() + planType.slice(1)} Subscription`,
    order_id:    order.id,
    prefill:     { name: user.name, email: user.email },
    theme:       { color: "#0ea5e9" },
    handler: async (response) => {
      // Step 4 — verify on backend
      const verifyRes = await fetch("/api/razorpay/verify", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(response),
      });
      if (verifyRes.ok) {
        onSuccess(response.razorpay_payment_id);
      } else {
        onError("Payment verification failed. Contact support@varextech.in");
      }
    },
    modal: { ondismiss: onDismiss },
  };

  new window.Razorpay(options).open();
}
