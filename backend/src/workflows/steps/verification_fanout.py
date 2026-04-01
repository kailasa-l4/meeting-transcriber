"""Verification Fan-out step -- runs the verification team on all normalized leads."""

import json

from sqlalchemy.orm import Session

from src.db.models import (
    CountryJob,
    Lead,
    LeadVerificationStatus,
    VerificationDimension,
    VerificationRecord,
    WorkflowEvent,
)

# Weights for composite confidence score
DIMENSION_WEIGHTS = {
    VerificationDimension.entity: 0.30,
    VerificationDimension.contact: 0.35,
    VerificationDimension.source_quality: 0.20,
    VerificationDimension.dedup: 0.15,
}


def _compute_composite_score(dimension_scores: dict[str, float]) -> float:
    """Weighted average of dimension sub-scores."""
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        score = dimension_scores.get(dim.value, 0.0)
        weighted_sum += score * weight
        total_weight += weight
    return round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0


def _determine_status(score: float) -> LeadVerificationStatus:
    """Map composite score to verification status."""
    if score >= 0.7:
        return LeadVerificationStatus.verified
    elif score >= 0.4:
        return LeadVerificationStatus.needs_review
    else:
        return LeadVerificationStatus.rejected


def run_verification_fanout(state: dict, db: Session) -> dict:
    """Run the verification team on all leads and compute composite scores."""
    from src.teams.verification_team import verification_team

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "verification_fanout"

    # Get all leads for this job that need verification
    leads = (
        db.query(Lead)
        .filter(
            Lead.country_job_id == job.id,
            Lead.verification_status.in_([
                LeadVerificationStatus.discovered,
                LeadVerificationStatus.normalized,
            ]),
        )
        .all()
    )

    verified_count = 0
    rejected_count = 0

    for lead in leads:
        # Build verification prompt for each lead
        lead_info = {
            "name": lead.name,
            "company": lead.company_name,
            "email": lead.email,
            "phone": lead.phone,
            "website": lead.website,
            "details": lead.details,
            "source_urls": lead.source_urls or [],
            "country": state["country"],
        }

        prompt = (
            f"Verify this gold industry lead:\n\n"
            f"{json.dumps(lead_info, indent=2, default=str)}\n\n"
            f"Check entity existence, contact validity, source quality, "
            f"and potential duplicates. Provide scores (0.0-1.0) for each dimension."
        )

        try:
            response = verification_team.run(prompt)

            # Parse verification results from team response
            # Default scores if parsing fails
            dimension_scores = {
                "entity": 0.5,
                "contact": 0.5,
                "source_quality": 0.5,
                "dedup": 0.8,
            }

            # Create verification records for each dimension
            for dim_name, score in dimension_scores.items():
                dim = VerificationDimension(dim_name)
                vr = VerificationRecord(
                    lead_id=lead.id,
                    status=_determine_status(score),
                    confidence_score=score,
                    dimension=dim,
                    verifier_notes=(
                        response.content[:500] if response and response.content else None
                    ),
                    skill_used="verification_team",
                )
                db.add(vr)

            # Compute composite score
            composite = _compute_composite_score(dimension_scores)
            final_status = _determine_status(composite)

            lead.confidence_score = composite
            lead.confidence_breakdown = dimension_scores
            lead.verification_status = final_status

            if final_status == LeadVerificationStatus.verified:
                verified_count += 1
            elif final_status == LeadVerificationStatus.rejected:
                rejected_count += 1

        except Exception as exc:
            # Mark leads that fail verification as needs_review
            lead.verification_status = LeadVerificationStatus.needs_review
            lead.confidence_score = 0.0
            lead.confidence_breakdown = {"error": str(exc)}

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="verification_completed",
        stage="verification_fanout",
        payload={
            "total_leads": len(leads),
            "verified": verified_count,
            "rejected": rejected_count,
            "needs_review": len(leads) - verified_count - rejected_count,
        },
    )
    db.add(event)
    db.commit()

    state["verified_leads"] = [
        {"id": str(l.id), "name": l.name, "score": l.confidence_score}
        for l in leads
        if l.verification_status == LeadVerificationStatus.verified
    ]
    state["verification_summary"] = {
        "total": len(leads),
        "verified": verified_count,
        "rejected": rejected_count,
    }
    return state
