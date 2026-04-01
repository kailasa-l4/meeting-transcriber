"""Intake step -- create CountryJob and initialize workflow state."""

import uuid

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, WorkflowEvent
from src.models.country_job import CountrySubmissionInput


def run_intake(input_data: CountrySubmissionInput, db: Session) -> dict:
    """Create a CountryJob record and return initial workflow state."""
    job = CountryJob(
        id=uuid.uuid4(),
        country=input_data.country,
        status=CountryJobStatus.queued,
        current_stage="intake",
        user_context=input_data.model_dump(exclude_none=True),
    )
    db.add(job)

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="intake",
        stage="intake",
        payload={"country": input_data.country},
    )
    db.add(event)
    db.commit()

    return {
        "job_id": str(job.id),
        "country": input_data.country,
        "user_context": input_data.model_dump(exclude_none=True),
        "leads": [],
        "verified_leads": [],
        "drafts": [],
    }
