# PATH: varex_backend/app/api/v1/team.py
# FIX 1.6: order_by(TeamMember.display_order) — column now exists after migration
# FIX 1.7: member.avatar_url — attribute now exists in model

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.team import TeamMember
from app.schemas.team import TeamMemberCreate, TeamMemberResponse, AvatarUpdatePayload
from app.dependencies.auth import get_current_active_user, require_admin
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[TeamMemberResponse])
async def list_team(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.is_published == True)
        .order_by(TeamMember.display_order)          # FIX 1.6 — column now in model
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=TeamMemberResponse)
async def get_member(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).where(TeamMember.slug == slug))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@router.post("/", response_model=TeamMemberResponse)
async def create_member(
    payload: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    member = TeamMember(**payload.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/{member_id}", response_model=TeamMemberResponse)
async def update_member(
    member_id: uuid.UUID,
    payload: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(member, k, v)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/{member_id}/avatar", response_model=TeamMemberResponse)
async def update_avatar(
    member_id: uuid.UUID,
    payload: AvatarUpdatePayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    member.avatar_url   = payload.avatar_url    # FIX 1.7 — column now in model
    member.avatar_s3_key = payload.avatar_s3_key
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def delete_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    await db.delete(member)
    await db.commit()
