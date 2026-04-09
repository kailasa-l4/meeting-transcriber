"""API router for Leads -- list, filter, and inspect verified leads."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import EmailDraft, Lead, LeadSource, VerificationRecord
from src.models.lead import LeadDetailResponse, LeadResponse, LeadSourceResponse
from src.models.verification import VerificationRecordResponse

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=list[LeadResponse])
def list_leads(
    job_id: UUID | None = Query(None, description="Filter by country job ID"),
    status: str | None = Query(None, description="Filter by verification status"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List leads sorted by confidence score descending."""
    query = db.query(Lead)
    if job_id:
        query = query.filter(Lead.country_job_id == job_id)
    if status:
        query = query.filter(Lead.verification_status == status)
    if min_confidence is not None:
        query = query.filter(Lead.confidence_score >= min_confidence)

    leads = (
        query.order_by(Lead.confidence_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return leads


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    """Get full lead detail with sources and verification records."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    sources = (
        db.query(LeadSource)
        .filter(LeadSource.lead_id == lead_id)
        .order_by(LeadSource.collected_at.desc())
        .all()
    )

    verification_records = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.lead_id == lead_id)
        .order_by(VerificationRecord.created_at.desc())
        .all()
    )

    # Check draft status
    latest_draft = (
        db.query(EmailDraft)
        .filter(EmailDraft.lead_id == lead_id)
        .order_by(EmailDraft.version_number.desc())
        .first()
    )
    draft_status = latest_draft.status.value if latest_draft else None

    return LeadDetailResponse(
        lead=LeadResponse.model_validate(lead),
        sources=[LeadSourceResponse.model_validate(s) for s in sources],
        verification_records=[
            VerificationRecordResponse.model_validate(v) for v in verification_records
        ],
        draft_status=draft_status,
    )
