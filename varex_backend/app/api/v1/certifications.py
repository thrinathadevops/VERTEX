from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_admin
from app.models.certification import Certification, Achievement, CertDomain
from app.models.user import User
from app.schemas.certification import (
    CertificationCreate, CertificationResponse,
    AchievementCreate, AchievementResponse,
)

router = APIRouter()

# ── Certifications ────────────────────────────────────────────────
@router.get("/", response_model=list[CertificationResponse])
async def list_certs(domain: CertDomain | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Certification).where(Certification.is_published == True)
    if domain:
        q = q.where(Certification.domain == domain)
    result = await db.execute(q.order_by(Certification.issued_date.desc()))
    return result.scalars().all()

@router.post("/", response_model=CertificationResponse, status_code=201)
async def create_cert(
    payload: CertificationCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cert = Certification(**payload.model_dump())
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert

# ── Achievements ──────────────────────────────────────────────────
@router.get("/achievements", response_model=list[AchievementResponse])
async def list_achievements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Achievement).where(Achievement.is_published == True).order_by(Achievement.year.desc())
    )
    return result.scalars().all()

@router.post("/achievements", response_model=AchievementResponse, status_code=201)
async def create_achievement(
    payload: AchievementCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    ach = Achievement(**payload.model_dump())
    db.add(ach)
    await db.commit()
    await db.refresh(ach)
    return ach
