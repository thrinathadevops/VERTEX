# PATH: varex_backend/app/services/subscription_service.py
# FIX: PlanType.annual -> PlanType.quarterly (Bug 1.5)
# FIX: PlanType.enterprise handled with None expiry (Bug 2.3)
# FIX: Idempotency — cancel existing active sub before creating new (Bug 2.2)

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.user import User, UserRole


PLAN_DURATIONS: dict[PlanType, timedelta | None] = {
    PlanType.monthly:    timedelta(days=30),
    PlanType.quarterly:  timedelta(days=90),   # was PlanType.annual — FIXED
    PlanType.enterprise: None,                  # manual expiry — FIXED
}

PLAN_ROLE_MAP: dict[PlanType, UserRole] = {
    PlanType.monthly:    UserRole.premium,
    PlanType.quarterly:  UserRole.premium,
    PlanType.enterprise: UserRole.enterprise,
}


async def create_subscription(
    user: User,
    plan_type: PlanType,
    razorpay_order_id: str,
    db: AsyncSession,
) -> Subscription:
    # Idempotency: cancel any existing active subscription first (Bug 2.2)
    existing_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .where(Subscription.status == SubscriptionStatus.active)
    )
    for existing in existing_result.scalars().all():
        existing.status = SubscriptionStatus.cancelled

    sub = Subscription(
        user_id=user.id,
        plan_type=plan_type,
        status=SubscriptionStatus.pending,
        razorpay_order_id=razorpay_order_id,
    )
    db.add(sub)
    await db.flush()
    return sub


async def activate_subscription(
    subscription: Subscription,
    razorpay_payment_id: str,
    db: AsyncSession,
) -> Subscription:
    duration = PLAN_DURATIONS[subscription.plan_type]

    subscription.status = SubscriptionStatus.active
    subscription.razorpay_payment_id = razorpay_payment_id
    subscription.start_date = datetime.utcnow()
    subscription.expiry_date = (datetime.utcnow() + duration) if duration else None

    # Upgrade user role
    result = await db.execute(select(User).where(User.id == subscription.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.role = PLAN_ROLE_MAP[subscription.plan_type]

    await db.commit()
    await db.refresh(subscription)
    return subscription


async def expire_subscriptions(db: AsyncSession) -> int:
    """Called by scheduler daily to expire overdue subscriptions."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Subscription)
        .where(Subscription.status == SubscriptionStatus.active)
        .where(Subscription.expiry_date < now)
        .where(Subscription.expiry_date.isnot(None))
    )
    count = 0
    for sub in result.scalars().all():
        sub.status = SubscriptionStatus.expired
        # Downgrade user role
        user_result = await db.execute(select(User).where(User.id == sub.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.role = UserRole.free_user
        count += 1
    await db.commit()
    return count
