"""Approval Wait step -- pauses the workflow for human review of drafts."""

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, WorkflowEvent


def run_approval_wait(state: dict, db: Session) -> dict:
    """Update job status to waiting_for_approval and pause the workflow.

    This step marks the boundary between automated processing and human review.
    The workflow pauses here until all drafts are approved/rejected via the API.
    """
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.status = CountryJobStatus.waiting_for_approval
    job.current_stage = "approval_wait"

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="waiting_for_approval",
        stage="approval_wait",
        payload={
            "draft_count": state.get("draft_count", 0),
            "message": "Workflow paused. Review and approve/reject drafts via the API.",
        },
    )
    db.add(event)
    db.commit()

    state["paused"] = True
    state["pause_reason"] = "waiting_for_approval"
    return state
