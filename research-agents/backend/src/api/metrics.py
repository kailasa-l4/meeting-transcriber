"""API router for Metrics -- aggregate statistics across jobs, leads, and drafts."""

from fastapi import APIRouter, Depends, HTTPException
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
    SkillInvocationLog,
)
from src.utils.token_tracker import get_session_cost_summary

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


class SkillStat(BaseModel):
    """Per-skill invocation statistics."""
    skill_name: str
    total_invocations: int
    avg_duration_ms: float
    error_count: int
    error_rate: float


class SkillMetricsResponse(BaseModel):
    """Response for skill invocation stats."""
    skills: list[SkillStat] = []


@router.get("/skills", response_model=SkillMetricsResponse)
def get_skill_metrics(db: Session = Depends(get_db)):
    """Return skill invocation stats: count, avg duration, error rate per skill."""
    rows = (
        db.query(
            SkillInvocationLog.skill_name,
            sa_func.count().label("total"),
            sa_func.avg(SkillInvocationLog.duration_ms).label("avg_dur"),
            sa_func.sum(
                sa_func.cast(SkillInvocationLog.status == "error", sa_func.Integer)
            ).label("err_count"),
        )
        .group_by(SkillInvocationLog.skill_name)
        .all()
    )

    skills = []
    for row in rows:
        total = row.total or 0
        err_count = row.err_count or 0
        skills.append(
            SkillStat(
                skill_name=row.skill_name,
                total_invocations=total,
                avg_duration_ms=round(float(row.avg_dur or 0), 2),
                error_count=err_count,
                error_rate=round(err_count / total, 4) if total > 0 else 0.0,
            )
        )

    return SkillMetricsResponse(skills=skills)


class CostSummaryResponse(BaseModel):
    """Token/cost summary for a job."""
    job_id: str
    total_tokens: int
    estimated_cost_usd: float
    country: str | None = None
    status: str | None = None


@router.get("/jobs/{job_id}/cost", response_model=CostSummaryResponse)
def get_job_cost(job_id: str, db: Session = Depends(get_db)):
    """Return token/cost summary for a specific job."""
    summary = get_session_cost_summary(db, job_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return CostSummaryResponse(**summary)
