from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_admin
from app.models.faq import FAQ, FAQCategory
from app.models.user import User
from app.schemas.faq import FAQCreate, FAQResponse

router = APIRouter()

@router.get("/", response_model=list[FAQResponse], summary="List FAQs (optionally by category)")
async def list_faqs(category: FAQCategory | None = None, db: AsyncSession = Depends(get_db)):
    q = select(FAQ).where(FAQ.is_published == True).order_by(FAQ.category, FAQ.order_rank)
    if category:
        q = q.where(FAQ.category == category)
    result = await db.execute(q)
    return result.scalars().all()

@router.post("/", response_model=FAQResponse, status_code=201, summary="Create FAQ (admin)")
async def create_faq(
    payload: FAQCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    faq = FAQ(**payload.model_dump())
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return faq

@router.put("/{faq_id}", response_model=FAQResponse, summary="Update FAQ (admin)")
async def update_faq(
    faq_id: UUID, payload: FAQCreate, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    faq = await db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(faq, k, v)
    await db.commit()
    await db.refresh(faq)
    return faq

@router.delete("/{faq_id}", status_code=204)
async def delete_faq(faq_id: UUID, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    faq = await db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(faq)
    await db.commit()
