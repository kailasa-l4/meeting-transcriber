"""SignalHire Enrichment step — enrich discovered leads with real contact data."""

import logging
import time

from sqlalchemy.orm import Session

from src.db.models import CountryJob, Lead, LeadSource, WorkflowEvent

logger = logging.getLogger(__name__)


def run_signalhire_enrichment(state: dict, db: Session) -> dict:
    """Enrich discovered leads using SignalHire Search API (free, no credits).

    For each lead with a company_name, searches SignalHire for real people
    at that company and merges any found contact data back into the lead.
    """
    from src.skills.signalhire.search import search_people, check_credits

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "signalhire_enrichment"
    db.commit()

    credits = check_credits()
    logger.info(f"SignalHire credits available: {credits}")

    leads = (
        db.query(Lead)
        .filter(Lead.country_job_id == job.id)
        .all()
    )

    country = state["country"]
    enriched_count = 0
    signalhire_profiles_found = 0

    for lead in leads:
        if not lead.company_name:
            continue

        # Search for people at this company in this country
        profiles = search_people(
            company=lead.company_name,
            location=country,
            title='("CEO" OR "Director" OR "Managing Director" OR "Head" OR "VP" OR "Manager")',
            size=5,
        )

        if not profiles:
            # Small delay to be polite to API
            time.sleep(0.5)
            continue

        signalhire_profiles_found += len(profiles)

        # Take the best matching profile (first result)
        best = profiles[0]

        # Update lead with enriched data
        if best.get("name") and best["name"] != lead.name:
            lead.details = (lead.details or "") + f"\nContact: {best['name']}"
            if best.get("role_title"):
                lead.role_title = best["role_title"]

        if best.get("linkedin_url"):
            # Store LinkedIn URL in source
            source = LeadSource(
                lead_id=lead.id,
                source_url=best["linkedin_url"],
                source_title=f"LinkedIn: {best.get('name', '')}",
                source_type="signalhire_search",
            )
            db.add(source)
            if not lead.source_urls:
                lead.source_urls = []
            lead.source_urls = lead.source_urls + [best["linkedin_url"]]
            lead.source_count = (lead.source_count or 0) + 1

        if best.get("company_website") and not lead.website:
            lead.website = best["company_website"]

        if best.get("headline"):
            lead.details = (lead.details or "") + f"\n{best['headline']}"

        if best.get("location"):
            lead.details = (lead.details or "") + f"\nLocation: {best['location']}"

        enriched_count += 1
        time.sleep(1)  # Rate limit: be polite

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="signalhire_enrichment_completed",
        stage="signalhire_enrichment",
        payload={
            "leads_processed": len(leads),
            "leads_enriched": enriched_count,
            "profiles_found": signalhire_profiles_found,
            "credits_remaining": credits,
        },
    )
    db.add(event)
    db.commit()

    logger.info(f"SignalHire enrichment: {enriched_count}/{len(leads)} leads enriched, {signalhire_profiles_found} profiles found")
    return state
