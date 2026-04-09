"""Intake step -- create CountryJob and initialize workflow state."""

import logging
import uuid

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, Lead, WorkflowEvent
from src.models.country_job import CountrySubmissionInput

logger = logging.getLogger(__name__)


def _find_prior_jobs(country: str, db: Session) -> list[CountryJob]:
    """Find all previous completed/partially-completed jobs for the same country."""
    return (
        db.query(CountryJob)
        .filter(
            CountryJob.country == country,
            CountryJob.status.in_([
                CountryJobStatus.completed,
                CountryJobStatus.partially_completed,
            ]),
        )
        .order_by(CountryJob.created_at.desc())
        .all()
    )


def _load_existing_leads(prior_jobs: list[CountryJob], db: Session) -> list[dict]:
    """Load emails and company names from prior jobs for dedup context."""
    if not prior_jobs:
        return []

    prior_job_ids = [j.id for j in prior_jobs]
    leads = (
        db.query(Lead.email, Lead.company_name, Lead.name)
        .filter(Lead.country_job_id.in_(prior_job_ids))
        .all()
    )
    return [
        {"email": l.email, "company_name": l.company_name, "name": l.name}
        for l in leads
    ]


def run_intake(input_data: CountrySubmissionInput, db: Session) -> dict:
    """Create a CountryJob record and return initial workflow state.

    If prior runs exist for the same country (and force_fresh_run is False),
    loads existing lead emails/company names for dedup context and stores
    prior_job_ids on the new job.
    """
    # Check for prior runs unless force_fresh_run is set
    prior_jobs: list[CountryJob] = []
    existing_leads: list[dict] = []
    prior_job_ids: list = []

    if not input_data.force_fresh_run:
        prior_jobs = _find_prior_jobs(input_data.country, db)
        if prior_jobs:
            prior_job_ids = [j.id for j in prior_jobs]
            existing_leads = _load_existing_leads(prior_jobs, db)
            logger.info(
                f"Found {len(prior_jobs)} prior job(s) for {input_data.country} "
                f"with {len(existing_leads)} existing leads for dedup"
            )

    job = CountryJob(
        id=uuid.uuid4(),
        country=input_data.country,
        status=CountryJobStatus.queued,
        current_stage="intake",
        user_context=input_data.model_dump(exclude_none=True),
        prior_job_ids=prior_job_ids if prior_job_ids else [],
    )
    db.add(job)

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="intake",
        stage="intake",
        payload={
            "country": input_data.country,
            "prior_job_count": len(prior_jobs),
            "existing_lead_count": len(existing_leads),
        },
    )
    db.add(event)
    db.commit()

    # Build exclusion list from existing leads and user-provided exclusions
    exclusion_emails = {l["email"] for l in existing_leads if l.get("email")}
    exclusion_companies = {l["company_name"] for l in existing_leads if l.get("company_name")}
    if input_data.exclusions:
        exclusion_companies.update(input_data.exclusions)

    return {
        "job_id": str(job.id),
        "country": input_data.country,
        "user_context": input_data.model_dump(exclude_none=True),
        "leads": [],
        "verified_leads": [],
        "drafts": [],
        "prior_job_ids": [str(jid) for jid in prior_job_ids],
        "existing_leads": existing_leads,
        "exclusion_emails": list(exclusion_emails),
        "exclusion_companies": list(exclusion_companies),
    }
