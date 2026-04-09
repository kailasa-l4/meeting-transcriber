"""Revision Loop step -- re-generates drafts incorporating structured feedback."""

import json
import uuid

from sqlalchemy.orm import Session

from src.db.models import (
    CountryJob,
    EmailDraft,
    Lead,
    OutreachStatus,
    WorkflowEvent,
)


def run_revision_loop(
    state: dict,
    db: Session,
    draft_id: str,
    feedback: dict,
) -> dict:
    """Re-run draft generation for a specific draft with revision feedback.

    Args:
        state: Current workflow state.
        db: Database session.
        draft_id: UUID of the draft to revise.
        feedback: Dict with keys: categories (list[str]), comments (str), guidance (str).
    """
    from src.agents.outreach.outreach_agent import outreach_agent

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "revision_loop"

    original_draft = db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
    if not original_draft:
        return state

    lead = db.query(Lead).filter(Lead.id == original_draft.lead_id).first()
    if not lead:
        return state

    # Mark original as being revised
    original_draft.status = OutreachStatus.draft_regenerating

    # Get the current max version for this lead
    max_version = (
        db.query(EmailDraft.version_number)
        .filter(
            EmailDraft.lead_id == lead.id,
            EmailDraft.country_job_id == job.id,
        )
        .order_by(EmailDraft.version_number.desc())
        .first()
    )
    next_version = (max_version[0] + 1) if max_version else 2

    user_ctx = state.get("user_context", {})
    tone = user_ctx.get("outreach_tone", "formal")
    template = user_ctx.get("template_family", "introduction")

    prompt = (
        f"Revise this outreach email draft based on feedback.\n\n"
        f"ORIGINAL DRAFT:\n"
        f"Subject: {original_draft.subject}\n"
        f"Body:\n{original_draft.body}\n\n"
        f"LEAD INFO:\n"
        f"Name: {lead.name}\n"
        f"Company: {lead.company_name}\n"
        f"Country: {state['country']}\n\n"
        f"FEEDBACK:\n{json.dumps(feedback, indent=2, default=str)}\n\n"
        f"Tone: {tone}\n"
        f"Template: {template}\n\n"
        f"Generate a revised version that addresses all feedback points."
    )

    try:
        response = outreach_agent.run(prompt)
        content = response.content if response and response.content else ""

        subject = original_draft.subject
        body = content

        if "Subject:" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("Subject:"):
                    subject = line.replace("Subject:", "").strip()
                    body = "\n".join(lines[i + 1 :]).strip()
                    break

        new_draft = EmailDraft(
            id=uuid.uuid4(),
            lead_id=lead.id,
            country_job_id=job.id,
            version_number=next_version,
            subject=subject,
            body=body,
            status=OutreachStatus.pending_review,
            model_name="moonshotai/kimi-k2.5",
            template_used=template,
            skill_used="outreach_agent_revision",
        )
        db.add(new_draft)

        # Mark original version as superseded
        original_draft.status = OutreachStatus.draft_regenerated

        event = WorkflowEvent(
            country_job_id=job.id,
            event_type="draft_revised",
            stage="revision_loop",
            payload={
                "draft_id": str(new_draft.id),
                "original_draft_id": draft_id,
                "version": next_version,
                "feedback_categories": feedback.get("categories", []),
            },
        )
        db.add(event)
        db.commit()

    except Exception as exc:
        event = WorkflowEvent(
            country_job_id=job.id,
            event_type="revision_failed",
            stage="revision_loop",
            payload={
                "draft_id": draft_id,
                "error": str(exc),
            },
        )
        db.add(event)
        db.commit()

    return state
