"""Final Send step -- sends approved drafts via GWS Gmail and completes the workflow."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.db.models import (
    CountryJob,
    CountryJobStatus,
    EmailDraft,
    EmailSendLog,
    Lead,
    OutreachStatus,
    WorkflowEvent,
)


def run_final_send(state: dict, db: Session) -> dict:
    """Send all approved drafts and mark the job as completed."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "final_send"

    # Get all approved drafts for this job
    approved_drafts = (
        db.query(EmailDraft)
        .filter(
            EmailDraft.country_job_id == job.id,
            EmailDraft.status == OutreachStatus.approved,
        )
        .all()
    )

    sent_count = 0
    failed_count = 0

    for draft in approved_drafts:
        lead = db.query(Lead).filter(Lead.id == draft.lead_id).first()
        if not lead or not lead.email:
            # Cannot send without an email address
            send_log = EmailSendLog(
                id=uuid.uuid4(),
                email_draft_id=draft.id,
                lead_id=draft.lead_id,
                send_method="gws_gmail",
                send_status="failed",
                failure_reason="No email address on lead",
            )
            db.add(send_log)
            failed_count += 1
            continue

        draft.status = OutreachStatus.sending

        try:
            from src.skills.gws.gmail_send import send_email_via_gmail

            result = send_email_via_gmail(
                to_email=lead.email,
                subject=draft.subject,
                body=draft.body,
            )

            send_log = EmailSendLog(
                id=uuid.uuid4(),
                email_draft_id=draft.id,
                lead_id=lead.id,
                send_method="gws_gmail",
                provider_message_id=result.get("message_id") if result else None,
                sent_at=datetime.now(timezone.utc),
                send_status="sent",
            )
            db.add(send_log)

            draft.status = OutreachStatus.sent
            sent_count += 1

        except Exception as exc:
            send_log = EmailSendLog(
                id=uuid.uuid4(),
                email_draft_id=draft.id,
                lead_id=lead.id,
                send_method="gws_gmail",
                send_status="failed",
                failure_reason=str(exc),
            )
            db.add(send_log)
            draft.status = OutreachStatus.send_failed
            failed_count += 1

    # Determine final job status
    if failed_count > 0 and sent_count > 0:
        job.status = CountryJobStatus.partially_completed
    elif sent_count > 0:
        job.status = CountryJobStatus.completed
    elif failed_count > 0:
        job.status = CountryJobStatus.failed
    else:
        # No approved drafts to send -- still mark as completed
        job.status = CountryJobStatus.completed

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="send_completed",
        stage="final_send",
        payload={
            "approved_drafts": len(approved_drafts),
            "sent": sent_count,
            "failed": failed_count,
        },
    )
    db.add(event)
    db.commit()

    state["send_summary"] = {
        "sent": sent_count,
        "failed": failed_count,
        "total_approved": len(approved_drafts),
    }
    state["paused"] = False
    return state
