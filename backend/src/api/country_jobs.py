"""API router for Country Jobs -- create, list, and inspect research jobs."""

import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import CountryJob, CountryJobStatus, Lead, LeadVerificationStatus, EmailDraft, OutreachStatus
from src.models.country_job import CountryJobResponse, CountryJobSummary, CountrySubmissionInput

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _enrich_summary(job: CountryJob, db: Session) -> dict:
    """Compute dynamic counts for a job summary."""
    lead_count = db.query(Lead).filter(Lead.country_job_id == job.id).count()
    verified_count = (
        db.query(Lead)
        .filter(
            Lead.country_job_id == job.id,
            Lead.verification_status == LeadVerificationStatus.verified,
        )
        .count()
    )
    from sqlalchemy import func as sa_func

    avg_row = (
        db.query(sa_func.avg(Lead.confidence_score))
        .filter(Lead.country_job_id == job.id, Lead.confidence_score > 0)
        .scalar()
    )
    avg_confidence = round(float(avg_row), 4) if avg_row else 0.0

    pending_drafts = (
        db.query(EmailDraft)
        .filter(
            EmailDraft.country_job_id == job.id,
            EmailDraft.status == OutreachStatus.pending_review,
        )
        .count()
    )
    sent_emails = (
        db.query(EmailDraft)
        .filter(
            EmailDraft.country_job_id == job.id,
            EmailDraft.status == OutreachStatus.sent,
        )
        .count()
    )

    return {
        "id": job.id,
        "country": job.country,
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "current_stage": job.current_stage,
        "lead_count": lead_count,
        "verified_count": verified_count,
        "avg_confidence": avg_confidence,
        "pending_drafts": pending_drafts,
        "sent_emails": sent_emails,
        "error_message": job.error_message,
        "total_token_count": job.total_token_count or 0,
        "estimated_cost": job.estimated_cost or 0.0,
    }


@router.get("/", response_model=list[CountryJobSummary])
def list_jobs(
    status: str | None = Query(None, description="Filter by job status"),
    country: str | None = Query(None, description="Filter by country (partial match)"),
    db: Session = Depends(get_db),
):
    """List all country research jobs with summary statistics."""
    query = db.query(CountryJob)
    if status:
        query = query.filter(CountryJob.status == status)
    if country:
        query = query.filter(CountryJob.country.ilike(f"%{country}%"))
    jobs = query.order_by(CountryJob.created_at.desc()).all()
    return [_enrich_summary(job, db) for job in jobs]


@router.get("/{job_id}", response_model=CountryJobResponse)
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    """Get full details for a specific job."""
    job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=CountryJobResponse, status_code=201)
def create_job(
    input_data: CountrySubmissionInput,
    db: Session = Depends(get_db),
):
    """Create a new country research job (intake step only).

    The full workflow pipeline can be triggered separately via /api/jobs/{id}/run.
    """
    from src.workflows.steps.intake import run_intake

    state = run_intake(input_data, db)
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    return job


def _run_workflow_pipeline(job_id: str) -> None:
    """Background task that runs the automated portion of the pipeline."""
    from src.db.base import SessionLocal
    from src.workflows.steps.knowledge_seeding import run_knowledge_seeding
    from src.workflows.steps.discovery_planning import run_discovery_planning
    from src.workflows.steps.discovery_fanout import run_discovery_fanout
    from src.workflows.steps.normalization import run_normalization
    from src.workflows.steps.verification_fanout import run_verification_fanout
    from src.workflows.steps.lead_persistence import run_lead_persistence
    from src.workflows.steps.draft_generation import run_draft_generation
    from src.workflows.steps.approval_wait import run_approval_wait

    db = SessionLocal()
    try:
        job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
        if not job:
            return

        state = {
            "job_id": str(job.id),
            "country": job.country,
            "user_context": job.user_context or {},
            "leads": [],
            "verified_leads": [],
            "drafts": [],
        }

        pipeline = [
            run_knowledge_seeding,
            run_discovery_planning,
            run_discovery_fanout,
            run_normalization,
            run_verification_fanout,
            run_lead_persistence,
            run_draft_generation,
            run_approval_wait,
        ]

        for step_fn in pipeline:
            state = step_fn(state, db)
            if state.get("paused"):
                break

    except Exception as exc:
        job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
        if job:
            job.status = CountryJobStatus.failed
            job.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("/{job_id}/run", response_model=CountryJobResponse)
def run_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger the full workflow pipeline for an existing job (runs in background)."""
    job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (CountryJobStatus.queued, CountryJobStatus.failed):
        raise HTTPException(
            status_code=409,
            detail=f"Job is in '{job.status.value}' state and cannot be re-run",
        )

    background_tasks.add_task(_run_workflow_pipeline, str(job.id))
    return job


@router.post("/{job_id}/send", response_model=CountryJobResponse)
def send_approved(job_id: UUID, db: Session = Depends(get_db)):
    """Send all approved drafts for a job (final_send step)."""
    from src.workflows.steps.final_send import run_final_send

    job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != CountryJobStatus.waiting_for_approval:
        raise HTTPException(
            status_code=409,
            detail=f"Job must be in 'waiting_for_approval' state, currently '{job.status.value}'",
        )

    state = {
        "job_id": str(job.id),
        "country": job.country,
        "user_context": job.user_context or {},
    }
    run_final_send(state, db)

    db.refresh(job)
    return job
