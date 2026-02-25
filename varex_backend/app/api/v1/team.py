from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import require_admin
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.team import AvatarUpdatePayload, TeamMemberCreate, TeamMemberResponse

router = APIRouter()


# Public

@router.get("/", response_model=list[TeamMemberResponse], summary="Public team listing")
async def list_team(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.is_published == True)
        .order_by(TeamMember.display_order)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=TeamMemberResponse, summary="Team member profile by slug")
async def get_member(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).where(TeamMember.slug == slug))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


# Admin

@router.post(
    "/",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add team member (admin)",
)
async def create_member(
    payload: TeamMemberCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    member = TeamMember(**payload.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.put(
    "/{member_id}",
    response_model=TeamMemberResponse,
    summary="Full update of a team member (admin)",
)
async def update_member(
    member_id: UUID,
    payload: TeamMemberCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    member = await db.get(TeamMember, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch(
    "/{member_id}/avatar",
    response_model=TeamMemberResponse,
    summary="Update team member avatar from S3 upload (admin)",
)
async def update_avatar(
    member_id: UUID,
    payload: AvatarUpdatePayload,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Saves the S3 public URL and key returned by the /api/s3/presign upload."""
    member = await db.get(TeamMember, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    if payload.avatar_url is not None:
        member.avatar_url = payload.avatar_url
    if payload.s3_key is not None:
        member.avatar_s3_key = payload.s3_key
    await db.commit()
    await db.refresh(member)
    return member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete team member (admin)",
)
async def delete_member(
    member_id: UUID,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    member = await db.get(TeamMember, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    await db.delete(member)
    await db.commit()