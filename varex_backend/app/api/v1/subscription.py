from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services.subscription_service import create_subscription, get_active_subscription

router = APIRouter()


@router.get("/me", response_model=SubscriptionResponse)
async def my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await get_active_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await create_subscription(db, current_user.id, payload.plan_type)
    return sub
