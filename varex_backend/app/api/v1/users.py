from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_own_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/admin/all", response_model=list[UserResponse])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()
