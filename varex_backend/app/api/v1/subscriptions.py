# PATH: varex_backend/app/api/v1/subscriptions.py
# FIX 2.1: settings.RAZORPAY_SECRET → settings.RAZORPAY_KEY_SECRET

import hmac, hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.models.subscription import Subscription, PlanType
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, ActivateSubscription
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.services.subscription_service import create_subscription, activate_subscription
import razorpay

router = APIRouter()


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    return sub


@router.post("/", response_model=SubscriptionResponse)
async def new_subscription(
    payload: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    plan_prices = {
        PlanType.monthly:    149900,   # paise
        PlanType.quarterly:  399900,
        PlanType.enterprise: 0,
    }
    amount = plan_prices.get(payload.plan_type, 0)

    # Create Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))  # FIX 2.1
    order  = client.order.create({"amount": amount, "currency": "INR", "receipt": str(current_user.id)})

    sub = await create_subscription(
        user=current_user,
        plan_type=payload.plan_type,
        razorpay_order_id=order["id"],
        db=db,
    )
    await db.commit()
    await db.refresh(sub)
    return sub


@router.patch("/activate", response_model=SubscriptionResponse)
async def activate_sub(
    payload: ActivateSubscription,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.id == payload.subscription_id)
        .where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Verify Razorpay signature
    body     = f"{sub.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),   # FIX 2.1
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    if expected != payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    sub = await activate_subscription(sub, payload.razorpay_payment_id, db)
    return sub
