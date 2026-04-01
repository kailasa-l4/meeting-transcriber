"""API router for Metrics -- aggregate statistics across jobs, leads, and drafts."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import (
    CountryJob,
    CountryJobStatus,
    EmailDraft,
    Lead,
    LeadVerificationStatus,
    OutreachStatus,
)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class SystemMetrics(BaseModel):
    """Aggregate metrics for the dashboard."""

    total_jobs: int = 0
    jobs_by_status: dict[str, int] = {}
    total_leads: int = 0
    verified_leads: int = 0
    avg_confidence: float = 0.0
    total_drafts: int = 0
    pending_drafts: int = 0
    approved_drafts: int = 0
    sent_emails: int = 0
    rejected_drafts: int = 0
    countries_covered: list[str] = []


@router.get("/", response_model=SystemMetrics)
def get_metrics(db: Session = Depends(get_db)):
    """Return aggregate metrics across all jobs."""
    # Job counts by status
    total_jobs = db.query(CountryJob).count()
    status_counts = (
        db.query(CountryJob.status, sa_func.count())
        .group_by(CountryJob.status)
        .all()
    )
    jobs_by_status = {
        status.value if hasattr(status, "value") else str(status): count
        for status, count in status_counts
    }

    # Lead counts
    total_leads = db.query(Lead).count()
    verified_leads = (
        db.query(Lead)
        .filter(Lead.verification_status == LeadVerificationStatus.verified)
        .count()
    )

    avg_row = (
        db.query(sa_func.avg(Lead.confidence_score))
        .filter(Lead.confidence_score > 0)
        .scalar()
    )
    avg_confidence = round(float(avg_row), 4) if avg_row else 0.0

    # Draft counts
    total_drafts = db.query(EmailDraft).count()
    pending_drafts = (
        db.query(EmailDraft)
        .filter(EmailDraft.status == OutreachStatus.pending_review)
        .count()
    )
    approved_drafts = (
        db.query(EmailDraft)
        .filter(EmailDraft.status == OutreachStatus.approved)
        .count()
    )
    sent_emails = (
        db.query(EmailDraft)
        .filter(EmailDraft.status == OutreachStatus.sent)
        .count()
    )
    rejected_drafts = (
        db.query(EmailDraft)
        .filter(EmailDraft.status == OutreachStatus.rejected)
        .count()
    )

    # Unique countries
    countries = (
        db.query(CountryJob.country)
        .distinct()
        .order_by(CountryJob.country)
        .all()
    )
    countries_covered = [c[0] for c in countries]

    return SystemMetrics(
        total_jobs=total_jobs,
        jobs_by_status=jobs_by_status,
        total_leads=total_leads,
        verified_leads=verified_leads,
        avg_confidence=avg_confidence,
        total_drafts=total_drafts,
        pending_drafts=pending_drafts,
        approved_drafts=approved_drafts,
        sent_emails=sent_emails,
        rejected_drafts=rejected_drafts,
        countries_covered=countries_covered,
    )
