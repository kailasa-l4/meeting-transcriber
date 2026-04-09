"""Lead Persistence step -- saves verified leads to xlsx file."""

import logging

from sqlalchemy.orm import Session

from src.db.models import CountryJob, Lead, LeadVerificationStatus, WorkflowEvent

logger = logging.getLogger(__name__)


def run_lead_persistence(state: dict, db: Session) -> dict:
    """Save verified leads to xlsx file and update job summary."""
    from src.skills.output.xlsx_writer import write_leads_to_xlsx

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "lead_persistence"

    leads = (
        db.query(Lead)
        .filter(
            Lead.country_job_id == job.id,
            Lead.verification_status.in_([
                LeadVerificationStatus.verified,
                LeadVerificationStatus.needs_review,
            ]),
        )
        .order_by(Lead.confidence_score.desc())
        .all()
    )

    xlsx_path = ""
    rows_written = 0

    if leads:
        lead_dicts = [
            {
                "name": l.name,
                "role_title": l.role_title or "",
                "company_name": l.company_name or "",
                "email": l.email or "",
                "phone": l.phone or "",
                "whatsapp": l.whatsapp or "",
                "website": l.website or "",
                "details": (l.details or "")[:300],
                "source_text": "; ".join(l.source_urls or []) or l.source_text or "",
                "linkedin_url": "",
                "location": "",
                "confidence_score": l.confidence_score,
            }
            for l in leads
        ]

        # Extract LinkedIn URLs from sources
        for i, lead in enumerate(leads):
            for url in (lead.source_urls or []):
                if "linkedin.com" in url:
                    lead_dicts[i]["linkedin_url"] = url
                    break

        try:
            xlsx_path = write_leads_to_xlsx(
                leads=lead_dicts,
                country=state["country"],
                job_id=state["job_id"],
            )
            rows_written = len(lead_dicts)
            logger.info(f"Wrote {rows_written} leads to {xlsx_path}")
        except Exception as exc:
            logger.error(f"Failed to write xlsx: {exc}")

    # Update job summary
    total_leads = db.query(Lead).filter(Lead.country_job_id == job.id).count()
    verified_count = (
        db.query(Lead)
        .filter(Lead.country_job_id == job.id, Lead.verification_status == LeadVerificationStatus.verified)
        .count()
    )

    job.summary_counts = {
        "total_leads": total_leads,
        "verified": verified_count,
        "xlsx_rows_written": rows_written,
        "xlsx_path": xlsx_path,
    }

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="leads_persisted",
        stage="lead_persistence",
        payload={
            "total_leads": total_leads,
            "verified": verified_count,
            "xlsx_rows_written": rows_written,
            "xlsx_path": xlsx_path,
        },
    )
    db.add(event)
    db.commit()

    state["xlsx_path"] = xlsx_path
    return state
