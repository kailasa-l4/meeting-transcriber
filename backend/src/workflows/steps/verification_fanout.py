"""Verification Fan-out step -- scores leads using heuristic verification."""

import re

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
    if score >= 0.6:
        return LeadVerificationStatus.verified
    elif score >= 0.3:
        return LeadVerificationStatus.needs_review
    else:
        return LeadVerificationStatus.rejected


def _score_entity(lead: Lead) -> tuple[float, str]:
    """Score entity plausibility based on available data."""
    score = 0.3  # base
    notes = []
    if lead.company_name and len(lead.company_name) > 3:
        score += 0.3
        notes.append("Has company name")
    if lead.name and lead.name != lead.company_name and len(lead.name) > 3:
        score += 0.2
        notes.append("Has distinct contact name")
    if lead.details and len(lead.details) > 20:
        score += 0.2
        notes.append("Has detailed description")
    return min(score, 1.0), "; ".join(notes) or "Minimal entity info"


def _score_contact(lead: Lead) -> tuple[float, str]:
    """Score contact info quality."""
    score = 0.1
    notes = []
    if lead.email and "@" in (lead.email or ""):
        score += 0.35
        notes.append(f"Has email: {lead.email}")
        # Bonus for non-generic emails
        if not any(g in lead.email for g in ["info@", "contact@", "admin@"]):
            score += 0.1
            notes.append("Non-generic email")
    if lead.phone and len(lead.phone or "") >= 8:
        score += 0.25
        notes.append("Has phone number")
    if lead.website and lead.website.startswith("http"):
        score += 0.2
        notes.append("Has website URL")
    if lead.whatsapp:
        score += 0.1
        notes.append("Has WhatsApp")
    return min(score, 1.0), "; ".join(notes) or "No contact info"


def _score_source(lead: Lead) -> tuple[float, str]:
    """Score source evidence quality."""
    score = 0.3  # base for being discovered
    notes = []
    if lead.source_text and len(lead.source_text) > 10:
        score += 0.3
        notes.append("Has source description")
    if lead.source_urls and len(lead.source_urls) > 0:
        score += 0.2
        notes.append(f"{len(lead.source_urls)} source URL(s)")
    if lead.source_count and lead.source_count > 1:
        score += 0.2
        notes.append("Multiple sources")
    return min(score, 1.0), "; ".join(notes) or "Minimal source info"


def _check_dedup(lead: Lead, existing_emails: set, existing_companies: set) -> tuple[float, str]:
    """Check for duplicates against existing leads."""
    if lead.email and lead.email.lower() in existing_emails:
        return 0.0, f"Duplicate email: {lead.email}"
    if lead.company_name:
        normalized = lead.company_name.lower().strip()
        for suffix in [" ltd", " limited", " inc", " corp", " co", " plc"]:
            normalized = normalized.removesuffix(suffix)
        if normalized.strip() in existing_companies:
            return 0.2, f"Similar company name found"
    return 1.0, "No duplicates found"


def run_verification_fanout(state: dict, db: Session) -> dict:
    """Score all leads using heuristic verification (fast, no LLM calls)."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "verification_fanout"

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

    # Build dedup sets from all leads in this batch
    seen_emails: set[str] = set()
    seen_companies: set[str] = set()

    verified_count = 0
    rejected_count = 0

    for lead in leads:
        # Score each dimension
        entity_score, entity_notes = _score_entity(lead)
        contact_score, contact_notes = _score_contact(lead)
        source_score, source_notes = _score_source(lead)
        dedup_score, dedup_notes = _check_dedup(lead, seen_emails, seen_companies)

        dimension_scores = {
            "entity": entity_score,
            "contact": contact_score,
            "source_quality": source_score,
            "dedup": dedup_score,
        }

        # Create verification records
        for dim_name, (score, notes) in [
            ("entity", (entity_score, entity_notes)),
            ("contact", (contact_score, contact_notes)),
            ("source_quality", (source_score, source_notes)),
            ("dedup", (dedup_score, dedup_notes)),
        ]:
            dim = VerificationDimension(dim_name)
            vr = VerificationRecord(
                lead_id=lead.id,
                status=_determine_status(score),
                confidence_score=score,
                dimension=dim,
                verifier_notes=notes,
                skill_used="heuristic_verification",
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

        # Track seen entities for dedup
        if lead.email:
            seen_emails.add(lead.email.lower())
        if lead.company_name:
            norm = lead.company_name.lower().strip()
            for suffix in [" ltd", " limited", " inc", " corp", " co", " plc"]:
                norm = norm.removesuffix(suffix)
            seen_companies.add(norm.strip())

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
