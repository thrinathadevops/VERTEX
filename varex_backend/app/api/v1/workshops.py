# PATH: varex_backend/app/api/v1/workshops.py
# FIX 2.8: seats_booked incremented on registration
# FIX 2.9: seat limit enforced (HTTP 409)
# FIX 2.10: duplicate registration returns HTTP 409

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.workshop import Workshop, WorkshopRegistration
from app.schemas.workshop import WorkshopCreate, WorkshopResponse, WorkshopRegistrationResponse
from app.dependencies.auth import get_current_active_user, require_admin
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[WorkshopResponse])
async def list_workshops(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workshop)
        .where(Workshop.is_published == True)
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=WorkshopResponse)
async def get_workshop(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workshop).where(Workshop.slug == slug))
    workshop = result.scalar_one_or_none()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop


@router.post("/", response_model=WorkshopResponse)
async def create_workshop(
    payload: WorkshopCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    workshop = Workshop(**payload.model_dump())
    db.add(workshop)
    await db.commit()
    await db.refresh(workshop)
    return workshop


@router.patch("/{workshop_id}", response_model=WorkshopResponse)
async def update_workshop(
    workshop_id: uuid.UUID,
    payload: WorkshopCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Workshop).where(Workshop.id == workshop_id))
    workshop = result.scalar_one_or_none()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(workshop, k, v)
    await db.commit()
    await db.refresh(workshop)
    return workshop


@router.delete("/{workshop_id}", status_code=204)
async def delete_workshop(
    workshop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Workshop).where(Workshop.id == workshop_id))
    workshop = result.scalar_one_or_none()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    await db.delete(workshop)
    await db.commit()


@router.post("/{workshop_id}/register", response_model=WorkshopRegistrationResponse)
async def register_for_workshop(
    workshop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Load workshop
    result = await db.execute(select(Workshop).where(Workshop.id == workshop_id))
    workshop = result.scalar_one_or_none()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    # FIX 2.9 — seat limit check
    if workshop.seats_booked >= workshop.max_seats:
        raise HTTPException(status_code=409, detail="Workshop is fully booked")

    # FIX 2.10 — duplicate registration check
    existing = await db.execute(
        select(WorkshopRegistration)
        .where(WorkshopRegistration.workshop_id == workshop_id)
        .where(WorkshopRegistration.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already registered for this workshop")

    # Create registration
    registration = WorkshopRegistration(
        workshop_id=workshop_id,
        user_id=current_user.id,
    )
    db.add(registration)

    # FIX 2.8 — increment seats_booked
    workshop.seats_booked += 1

    # Auto-mark as full if needed
    if workshop.seats_booked >= workshop.max_seats:
        workshop.status = "full"

    await db.commit()
    await db.refresh(registration)
    return registration


@router.get("/{workshop_id}/registrations", response_model=list[WorkshopRegistrationResponse])
async def get_registrations(
    workshop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(WorkshopRegistration).where(WorkshopRegistration.workshop_id == workshop_id)
    )
    return result.scalars().all()
