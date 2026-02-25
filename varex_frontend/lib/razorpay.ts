// PATH: varex_frontend/lib/razorpay.ts
// FIX 2.5: initiatePayment opens Razorpay modal AND calls /api/razorpay/verify on success

declare global {
  interface Window {
    Razorpay: any;
  }
}

function loadRazorpayScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) { resolve(); return; }
    const script = document.createElement("script");
    script.src   = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload  = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay SDK"));
    document.body.appendChild(script);
  });
}

interface PaymentOptions {
  order_id:       string;
  subscription_id: string;
  amount:         number;      // in paise
  user_name:      string;
  user_email:     string;
}

export function initiatePayment(opts: PaymentOptions): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      await loadRazorpayScript();

      const rzp = new window.Razorpay({
        key:         process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID!,
        amount:      opts.amount,
        currency:    "INR",
        name:        "VAREX Technologies",
        description: "Premium Subscription",
        order_id:    opts.order_id,
        prefill: {
          name:  opts.user_name,
          email: opts.user_email,
        },
        theme: { color: "#0ea5e9" },

        handler: async (response: {
          razorpay_order_id:   string;
          razorpay_payment_id: string;
          razorpay_signature:  string;
        }) => {
          try {
            // Verify payment signature server-side and activate subscription
            const verifyRes = await fetch("/api/razorpay/verify", {
              method:  "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                razorpay_order_id:   response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature:  response.razorpay_signature,
                subscription_id:     opts.subscription_id,
              }),
            });
            if (!verifyRes.ok) throw new Error("Payment verification failed");
            resolve();
          } catch (e) {
            reject(e);
          }
        },

        modal: {
          ondismiss: () => reject(new Error("Payment cancelled")),
        },
      });

      rzp.open();
    } catch (e) {
      reject(e);
    }
  });
}
