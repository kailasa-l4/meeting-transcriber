"""Draft Generation step -- runs outreach agent for eligible leads."""

import json
import uuid

from sqlalchemy.orm import Session

from src.db.models import (
    CountryJob,
    EmailDraft,
    Lead,
    LeadVerificationStatus,
    OutreachStatus,
    WorkflowEvent,
)

# Minimum confidence to generate a draft
DRAFT_CONFIDENCE_THRESHOLD = 0.6


def run_draft_generation(
    state: dict, db: Session, confidence_threshold: float | None = None
) -> dict:
    """Generate outreach email drafts for leads above the confidence threshold."""
    from src.agents.outreach.outreach_agent import outreach_agent

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "draft_generation"

    threshold = confidence_threshold or DRAFT_CONFIDENCE_THRESHOLD

    # Get verified leads above threshold that don't already have drafts
    eligible_leads = (
        db.query(Lead)
        .filter(
            Lead.country_job_id == job.id,
            Lead.verification_status == LeadVerificationStatus.verified,
            Lead.confidence_score >= threshold,
        )
        .order_by(Lead.confidence_score.desc())
        .all()
    )

    # Exclude leads that already have a draft
    existing_draft_lead_ids = {
        d.lead_id
        for d in db.query(EmailDraft.lead_id)
        .filter(EmailDraft.country_job_id == job.id)
        .all()
    }
    eligible_leads = [l for l in eligible_leads if l.id not in existing_draft_lead_ids]

    drafts_created = 0
    user_ctx = state.get("user_context", {})

    for lead in eligible_leads:
        lead_info = {
            "lead_name": lead.name,
            "company_name": lead.company_name,
            "country": state["country"],
            "email": lead.email,
            "role_title": lead.role_title,
            "details": lead.details,
            "confidence_score": lead.confidence_score,
        }

        tone = user_ctx.get("outreach_tone", "formal")
        template = user_ctx.get("template_family", "introduction")

        prompt = (
            f"Generate a personalized outreach email for this gold industry lead:\n\n"
            f"{json.dumps(lead_info, indent=2, default=str)}\n\n"
            f"Tone: {tone}\n"
            f"Template style: {template}\n"
            f"The email should introduce our gold banking partnership opportunity."
        )

        # Add revision context if present (for re-generation after feedback)
        feedback_ctx = state.get("feedback_context")
        if feedback_ctx:
            prompt += (
                f"\n\nPrevious feedback to incorporate:\n"
                f"{json.dumps(feedback_ctx, indent=2, default=str)}"
            )

        try:
            response = outreach_agent.run(prompt)
            content = response.content if response and response.content else ""

            # Parse subject and body from response
            subject = f"Gold Banking Partnership - {lead.company_name or lead.name}"
            body = content

            # Try to extract subject from response if formatted
            if "Subject:" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith("Subject:"):
                        subject = line.replace("Subject:", "").strip()
                        body = "\n".join(lines[i + 1 :]).strip()
                        break

            draft = EmailDraft(
                id=uuid.uuid4(),
                lead_id=lead.id,
                country_job_id=job.id,
                version_number=1,
                subject=subject,
                body=body,
                status=OutreachStatus.pending_review,
                model_name="moonshotai/kimi-k2.5",
                template_used=template,
                skill_used="outreach_agent",
            )
            db.add(draft)
            drafts_created += 1

        except Exception:
            # Skip leads where draft generation fails
            continue

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="drafts_generated",
        stage="draft_generation",
        payload={
            "eligible_leads": len(eligible_leads),
            "drafts_created": drafts_created,
            "threshold": threshold,
        },
    )
    db.add(event)
    db.commit()

    state["drafts"] = [
        {"lead_id": str(l.id), "name": l.name} for l in eligible_leads[:drafts_created]
    ]
    state["draft_count"] = drafts_created
    return state
