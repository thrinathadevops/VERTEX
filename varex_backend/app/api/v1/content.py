from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user, require_premium, require_admin
from app.models.content import Content, AccessLevel
from app.models.user import User, UserRole
from app.schemas.content import ContentCreate, ContentResponse

router = APIRouter()


@router.get("/free", response_model=list[ContentResponse])
async def list_free_content(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Content)
        .where(Content.access_level == AccessLevel.free)
        .where(Content.is_published == True)
    )
    return result.scalars().all()


@router.get("/premium", response_model=list[ContentResponse])
async def list_premium_content(
    _: User = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.is_published == True))
    return result.scalars().all()


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    payload: ContentCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    content = Content(**payload.model_dump())
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.access_level == AccessLevel.premium and current_user.role not in (
        UserRole.premium_user, UserRole.admin
    ):
        raise HTTPException(status_code=403, detail="Premium subscription required")
    return content
