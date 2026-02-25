from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies.auth import require_admin
from app.models.lead import ConsultationLead, LeadStatus
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadResponse
import logging

logger = logging.getLogger("varex.leads")
router = APIRouter()

async def _send_confirmation_email(name: str, email: str, service: str):
    """Background task: send confirmation email (wire SendGrid/SES here)."""
    logger.info("Confirmation email → %s (%s) for %s", name, email, service)
    # TODO: integrate email provider

@router.post("/", response_model=LeadResponse, status_code=201,
             summary="Submit consultation / contact form (public)")
async def submit_lead(
    payload: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — captures any incoming lead (contact, free consultation, etc.).
    Fires a background email confirmation.
    """
    lead = ConsultationLead(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    background_tasks.add_task(
        _send_confirmation_email, lead.name, lead.email, lead.service_interest.value
    )
    return lead

@router.get("/", response_model=list[LeadResponse], summary="List all leads (admin)")
async def list_leads(
    status: LeadStatus | None = None,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(ConsultationLead).order_by(ConsultationLead.created_at.desc())
    if status:
        q = q.where(ConsultationLead.status == status)
    result = await db.execute(q)
    return result.scalars().all()

@router.patch("/{lead_id}/status", summary="Update lead status (admin)")
async def update_lead_status(
    lead_id: UUID,
    new_status: LeadStatus,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(ConsultationLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = new_status
    await db.commit()
    return {"id": lead_id, "status": new_status}
