"""API router for Approvals -- review, approve, revise, and reject email drafts."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import (
    CountryJob,
    DraftReviewAction,
    EmailDraft,
    Lead,
    OutreachStatus,
    ReviewAction,
)
from src.models.email_draft import (
    DraftDetailResponse,
    DraftReviewActionResponse,
    DraftReviewRequest,
    EmailDraftResponse,
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending", response_model=list[DraftDetailResponse])
def list_pending(db: Session = Depends(get_db)):
    """List all drafts awaiting review, sorted by lead confidence descending."""
    pending_drafts = (
        db.query(EmailDraft)
        .filter(EmailDraft.status == OutreachStatus.pending_review)
        .all()
    )

    results = []
    for draft in pending_drafts:
        lead = db.query(Lead).filter(Lead.id == draft.lead_id).first()
        job = db.query(CountryJob).filter(CountryJob.id == draft.country_job_id).first()

        # Get all versions for this lead + job
        all_versions = (
            db.query(EmailDraft)
            .filter(
                EmailDraft.lead_id == draft.lead_id,
                EmailDraft.country_job_id == draft.country_job_id,
            )
            .order_by(EmailDraft.version_number.desc())
            .all()
        )

        # Get review history
        review_history = (
            db.query(DraftReviewAction)
            .filter(DraftReviewAction.email_draft_id.in_([v.id for v in all_versions]))
            .order_by(DraftReviewAction.created_at.desc())
            .all()
        )

        results.append(
            DraftDetailResponse(
                draft=EmailDraftResponse.model_validate(draft),
                lead_name=lead.name if lead else "Unknown",
                company_name=lead.company_name if lead else None,
                country=job.country if job else "Unknown",
                confidence_score=lead.confidence_score if lead else 0.0,
                template_used=draft.template_used,
                all_versions=[EmailDraftResponse.model_validate(v) for v in all_versions],
                review_history=[
                    DraftReviewActionResponse.model_validate(r) for r in review_history
                ],
            )
        )

    # Sort by confidence descending
    results.sort(key=lambda r: r.confidence_score, reverse=True)
    return results


@router.get("/{draft_id}", response_model=DraftDetailResponse)
def get_draft(draft_id: UUID, db: Session = Depends(get_db)):
    """Get full draft detail with version history and review actions."""
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    lead = db.query(Lead).filter(Lead.id == draft.lead_id).first()
    job = db.query(CountryJob).filter(CountryJob.id == draft.country_job_id).first()

    all_versions = (
        db.query(EmailDraft)
        .filter(
            EmailDraft.lead_id == draft.lead_id,
            EmailDraft.country_job_id == draft.country_job_id,
        )
        .order_by(EmailDraft.version_number.desc())
        .all()
    )

    review_history = (
        db.query(DraftReviewAction)
        .filter(DraftReviewAction.email_draft_id.in_([v.id for v in all_versions]))
        .order_by(DraftReviewAction.created_at.desc())
        .all()
    )

    return DraftDetailResponse(
        draft=EmailDraftResponse.model_validate(draft),
        lead_name=lead.name if lead else "Unknown",
        company_name=lead.company_name if lead else None,
        country=job.country if job else "Unknown",
        confidence_score=lead.confidence_score if lead else 0.0,
        template_used=draft.template_used,
        all_versions=[EmailDraftResponse.model_validate(v) for v in all_versions],
        review_history=[DraftReviewActionResponse.model_validate(r) for r in review_history],
    )


@router.post("/{draft_id}/approve", response_model=EmailDraftResponse)
def approve_draft(draft_id: UUID, db: Session = Depends(get_db)):
    """Approve a draft for sending."""
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != OutreachStatus.pending_review:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is in '{draft.status.value}' state and cannot be approved",
        )

    draft.status = OutreachStatus.approved

    review = DraftReviewAction(
        id=uuid.uuid4(),
        email_draft_id=draft.id,
        reviewer_id="api_user",
        action=ReviewAction.approve,
    )
    db.add(review)
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/request-changes", response_model=EmailDraftResponse)
def request_changes(
    draft_id: UUID, request: DraftReviewRequest, db: Session = Depends(get_db)
):
    """Submit structured feedback and trigger a draft revision."""
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status not in (OutreachStatus.pending_review, OutreachStatus.draft_regenerated):
        raise HTTPException(
            status_code=409,
            detail=f"Draft is in '{draft.status.value}' state and cannot receive changes",
        )

    draft.status = OutreachStatus.changes_requested

    review = DraftReviewAction(
        id=uuid.uuid4(),
        email_draft_id=draft.id,
        reviewer_id="api_user",
        action=ReviewAction.request_changes,
        structured_feedback_categories=[c.value for c in request.structured_feedback_categories],
        comments=request.comments,
    )
    db.add(review)
    db.commit()

    # Trigger revision
    from src.workflows.steps.revision_loop import run_revision_loop

    job = db.query(CountryJob).filter(CountryJob.id == draft.country_job_id).first()
    state = {
        "job_id": str(job.id),
        "country": job.country,
        "user_context": job.user_context or {},
    }
    feedback = {
        "categories": [c.value for c in request.structured_feedback_categories],
        "comments": request.comments,
        "guidance": request.guidance,
    }
    run_revision_loop(state, db, draft_id=str(draft.id), feedback=feedback)

    db.refresh(draft)
    return draft


@router.post("/{draft_id}/reject", response_model=EmailDraftResponse)
def reject_draft(
    draft_id: UUID,
    request: DraftReviewRequest | None = None,
    db: Session = Depends(get_db),
):
    """Reject a draft -- it will not be sent."""
    draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status not in (
        OutreachStatus.pending_review,
        OutreachStatus.draft_regenerated,
        OutreachStatus.changes_requested,
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Draft is in '{draft.status.value}' state and cannot be rejected",
        )

    draft.status = OutreachStatus.rejected

    review = DraftReviewAction(
        id=uuid.uuid4(),
        email_draft_id=draft.id,
        reviewer_id="api_user",
        action=ReviewAction.reject,
        comments=request.comments if request else None,
    )
    db.add(review)
    db.commit()
    db.refresh(draft)
    return draft
