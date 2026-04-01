"""Lead Persistence step -- syncs verified leads to Google Sheet via GWS skill."""

from sqlalchemy.orm import Session

from src.db.models import CountryJob, Lead, LeadVerificationStatus, WorkflowEvent


def run_lead_persistence(state: dict, db: Session) -> dict:
    """Sync verified leads to the Google Sheet and update job summary."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "lead_persistence"

    # Get all verified/needs_review leads for this job
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

    sheet_rows_written = 0

    # Attempt to write leads to the Google Sheet
    try:
        from src.skills.gws.sheets_append import append_leads_to_sheet

        rows = []
        for lead in leads:
            rows.append({
                "name": lead.name,
                "company": lead.company_name or "",
                "email": lead.email or "",
                "phone": lead.phone or "",
                "country": state["country"],
                "confidence": lead.confidence_score,
                "status": lead.verification_status.value,
                "source": "; ".join(lead.source_urls or []),
            })

        if rows:
            append_leads_to_sheet(rows, state["country"])
            sheet_rows_written = len(rows)
    except Exception:
        # Sheet sync is best-effort; the leads are already in the app DB
        pass

    # Update job summary counts
    total_leads = (
        db.query(Lead).filter(Lead.country_job_id == job.id).count()
    )
    verified_count = (
        db.query(Lead)
        .filter(
            Lead.country_job_id == job.id,
            Lead.verification_status == LeadVerificationStatus.verified,
        )
        .count()
    )
    avg_confidence = 0.0
    if leads:
        avg_confidence = round(sum(l.confidence_score for l in leads) / len(leads), 4)

    job.summary_counts = {
        "total_leads": total_leads,
        "verified": verified_count,
        "avg_confidence": avg_confidence,
        "sheet_rows_written": sheet_rows_written,
    }

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="leads_persisted",
        stage="lead_persistence",
        payload={
            "total_leads": total_leads,
            "verified": verified_count,
            "sheet_rows_written": sheet_rows_written,
        },
    )
    db.add(event)
    db.commit()

    state["persistence_summary"] = {
        "total_leads": total_leads,
        "verified": verified_count,
        "sheet_rows_written": sheet_rows_written,
    }
    return state
