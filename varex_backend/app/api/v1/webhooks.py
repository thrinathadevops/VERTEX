from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings

router = APIRouter()

@router.post("/razorpay", summary="Razorpay Webhook endpoint")
async def razorpay_webhook(request: Request):
    """
    Called by Razorpay (via frontend proxy) when a payment is successful,
    a subscription is halted, or other server-to-server webhook events.
    """
    signature = request.headers.get("x-razorpay-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    body = await request.body()
    
    # Example logic: in a real application you would use razorpay.Utility.verify_webhook_signature
    # import razorpay
    # client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    # try:
    #     client.utility.verify_webhook_signature(body.decode('utf-8'), signature, settings.RAZORPAY_WEBHOOK_SECRET)
    # except razorpay.errors.SignatureVerificationError:
    #     raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process event
    # payload = await request.json()
    # if payload["event"] == "subscription.charged":
    #     # update subscription status...
    #     pass

    return {"status": "ok"}
