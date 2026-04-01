"""Normalization step -- normalizes raw candidates into structured leads."""

import json
import uuid

from sqlalchemy.orm import Session

from src.db.models import CountryJob, Lead, LeadSource, LeadVerificationStatus, WorkflowEvent
from src.models.lead import NormalizedLead


def _parse_candidates_from_text(raw_text: str, country: str) -> list[dict]:
    """Attempt to parse structured lead data from raw discovery output.

    The discovery team returns markdown/text with lead information.
    This function tries to extract structured data. In production,
    a normalization skill (LLM-based) would handle this more robustly.
    """
    # Try JSON extraction first
    candidates = []
    try:
        # Look for JSON arrays in the text
        start = raw_text.find("[")
        end = raw_text.rfind("]")
        if start != -1 and end != -1:
            parsed = json.loads(raw_text[start : end + 1])
            if isinstance(parsed, list):
                return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: return the raw text as a single candidate for LLM normalization
    candidates.append({
        "name": "Unparsed Discovery Batch",
        "details": raw_text[:2000],
        "source_text": f"Discovery output for {country}",
        "needs_llm_normalization": True,
    })
    return candidates


def run_normalization(state: dict, db: Session) -> dict:
    """Normalize raw candidates into NormalizedLead records and persist to DB."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "normalization"

    raw_candidates = state.get("raw_candidates", [])
    normalized_leads = []
    persisted_count = 0

    for batch in raw_candidates:
        raw_text = batch.get("raw_text", "")
        parsed = _parse_candidates_from_text(raw_text, state["country"])

        for candidate in parsed:
            # Skip entries that are just parse failures
            if candidate.get("needs_llm_normalization"):
                # Store raw text as a single lead placeholder for manual review
                lead = Lead(
                    id=uuid.uuid4(),
                    country_job_id=uuid.UUID(state["job_id"]),
                    name=candidate.get("name", "Unknown"),
                    details=candidate.get("details"),
                    source_text=candidate.get("source_text"),
                    verification_status=LeadVerificationStatus.discovered,
                    confidence_score=0.0,
                )
                db.add(lead)
                persisted_count += 1
                continue

            # Build a NormalizedLead from parsed data
            try:
                nl = NormalizedLead(
                    name=candidate.get("name", "Unknown"),
                    role_title=candidate.get("role_title"),
                    whatsapp=candidate.get("whatsapp"),
                    phone=candidate.get("phone"),
                    details=candidate.get("details"),
                    email=candidate.get("email"),
                    company_name=candidate.get("company_name"),
                    website=candidate.get("website"),
                    source_text=candidate.get("source_text"),
                    source_urls=candidate.get("source_urls", []),
                    source_count=len(candidate.get("source_urls", [])),
                    discovery_skill_used=candidate.get("discovery_skill"),
                )
                normalized_leads.append(nl)

                # Persist to DB
                lead = Lead(
                    id=uuid.uuid4(),
                    country_job_id=uuid.UUID(state["job_id"]),
                    name=nl.name,
                    role_title=nl.role_title,
                    whatsapp=nl.whatsapp,
                    phone=nl.phone,
                    details=nl.details,
                    email=nl.email,
                    company_name=nl.company_name,
                    website=nl.website,
                    source_text=nl.source_text,
                    source_urls=nl.source_urls,
                    source_count=nl.source_count,
                    verification_status=LeadVerificationStatus.normalized,
                    confidence_score=0.0,
                    discovery_skill_used=nl.discovery_skill_used,
                )
                db.add(lead)

                # Persist source evidence
                for url in nl.source_urls:
                    source = LeadSource(
                        lead_id=lead.id,
                        source_url=url,
                        source_type="discovery",
                    )
                    db.add(source)

                persisted_count += 1

            except Exception:
                # Skip malformed candidates
                continue

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="normalization_completed",
        stage="normalization",
        payload={
            "raw_batches_processed": len(raw_candidates),
            "normalized_count": len(normalized_leads),
            "persisted_count": persisted_count,
        },
    )
    db.add(event)
    db.commit()

    state["leads"] = [nl.model_dump() for nl in normalized_leads]
    state["lead_count"] = persisted_count
    return state
