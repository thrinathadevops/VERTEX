# PATH: varex_backend/app/api/v1/analytics.py
# FIX 1.8: require_admin imported from correct module

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.dependencies.auth import require_admin          # FIX: was app.core.security
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.lead import ConsultationLead
from app.models.workshop import WorkshopRegistration
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/", summary="Platform analytics (admin only)")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    now     = datetime.utcnow()
    ago_30d = now - timedelta(days=30)

    # Users
    total_users  = (await db.execute(select(func.count(User.id)))).scalar()
    new_users    = (await db.execute(select(func.count(User.id)).where(User.created_at >= ago_30d))).scalar()
    premium_cnt  = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.premium))).scalar()
    enterprise_cnt = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.enterprise))).scalar()

    # Leads
    total_leads  = (await db.execute(select(func.count(ConsultationLead.id)))).scalar()
    new_leads    = (await db.execute(select(func.count(ConsultationLead.id)).where(ConsultationLead.created_at >= ago_30d))).scalar()
    converted    = (await db.execute(select(func.count(ConsultationLead.id)).where(ConsultationLead.status == "converted"))).scalar()

    # Subscriptions
    active_subs  = (await db.execute(select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.active))).scalar()

    # Workshops
    total_regs   = (await db.execute(select(func.count(WorkshopRegistration.id)))).scalar()

    return {
        "users": {
            "total":      total_users,
            "new_30d":    new_users,
            "premium":    premium_cnt,
            "enterprise": enterprise_cnt,
        },
        "leads": {
            "total":           total_leads,
            "new_30d":         new_leads,
            "converted":       converted,
            "conversion_rate": round((converted / total_leads * 100), 1) if total_leads else 0,
        },
        "subscriptions": { "active": active_subs },
        "workshops":     { "total_registrations": total_regs },
    }
