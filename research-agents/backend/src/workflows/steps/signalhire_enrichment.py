"""SignalHire Enrichment step — find real people at discovered companies."""

import logging
import time
import uuid

from sqlalchemy.orm import Session

from src.db.models import CountryJob, Lead, LeadSource, LeadVerificationStatus, WorkflowEvent

logger = logging.getLogger(__name__)


def run_signalhire_enrichment(state: dict, db: Session) -> dict:
    """For each discovered company, find ALL real people via SignalHire Search API.

    Creates a new lead for every person found. The original company-level leads
    are kept but each SignalHire person becomes their own lead row with:
    - Person's name as the lead name
    - Company name preserved
    - Role/title from their profile
    - LinkedIn URL as source
    """
    from src.skills.signalhire.search import search_people, check_credits

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "signalhire_enrichment"
    db.commit()

    credits = check_credits()
    logger.info(f"SignalHire credits available: {credits}")

    # Get company-level leads from discovery
    company_leads = (
        db.query(Lead)
        .filter(Lead.country_job_id == job.id)
        .all()
    )

    country = state["country"]
    total_people_found = 0
    people_leads_created = 0

    for company_lead in company_leads:
        if not company_lead.company_name:
            continue

        # Search for real people at this company
        profiles = search_people(
            company=company_lead.company_name,
            location=country,
            title='("CEO" OR "Director" OR "Managing Director" OR "Head" OR "VP" OR "Manager" OR "Officer")',
            size=25,
        )

        # If no results, try a broader search with just the core company name
        if not profiles:
            # Strip suffixes like "Limited", "Ltd", "Corporation", "PLC" for broader match
            short_name = company_lead.company_name
            for suffix in [" Limited", " Ltd", " Corporation", " Corp", " PLC", " Inc", " Co"]:
                short_name = short_name.replace(suffix, "").replace(suffix.lower(), "")
            short_name = short_name.strip()

            if short_name != company_lead.company_name:
                profiles = search_people(
                    company=short_name,
                    location=country,
                    keywords="gold mining",
                    size=25,
                )

        if not profiles:
            time.sleep(0.5)
            continue

        total_people_found += len(profiles)

        # Create a separate lead for EACH person found
        for profile in profiles:
            person_name = profile.get("name", "").strip()
            if not person_name:
                continue

            # Build details from profile data
            details_parts = []
            if profile.get("headline"):
                details_parts.append(profile["headline"])
            if profile.get("location"):
                details_parts.append(f"Location: {profile['location']}")
            if profile.get("industry"):
                details_parts.append(f"Industry: {profile['industry']}")

            # Create the person lead
            person_lead = Lead(
                id=uuid.uuid4(),
                country_job_id=job.id,
                name=person_name,
                role_title=profile.get("role_title", ""),
                company_name=company_lead.company_name,
                website=profile.get("company_website") or company_lead.website,
                email=company_lead.email,  # Keep company email until we have personal
                phone=company_lead.phone,
                details="\n".join(details_parts) if details_parts else company_lead.details,
                source_text=f"SignalHire search for {company_lead.company_name} in {country}",
                source_urls=[profile["linkedin_url"]] if profile.get("linkedin_url") else [],
                source_count=1 if profile.get("linkedin_url") else 0,
                verification_status=LeadVerificationStatus.normalized,
                confidence_score=0.0,
                discovery_skill_used="signalhire_search",
            )
            db.add(person_lead)
            people_leads_created += 1

            # Add LinkedIn as source evidence
            if profile.get("linkedin_url"):
                source = LeadSource(
                    lead_id=person_lead.id,
                    source_url=profile["linkedin_url"],
                    source_title=f"LinkedIn: {person_name}",
                    source_type="signalhire_search",
                )
                db.add(source)

        time.sleep(1)  # Rate limit politeness

    # Remove original company-level leads ONLY for companies where we found people
    # Keep company leads that had no SignalHire results
    if people_leads_created > 0:
        companies_with_people = set()
        for lead in db.query(Lead).filter(
            Lead.country_job_id == job.id,
            Lead.discovery_skill_used == "signalhire_search",
        ).all():
            companies_with_people.add(lead.company_name)

        for company_lead in company_leads:
            if company_lead.company_name in companies_with_people:
                db.delete(company_lead)

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="signalhire_enrichment_completed",
        stage="signalhire_enrichment",
        payload={
            "companies_searched": len(company_leads),
            "people_found": total_people_found,
            "people_leads_created": people_leads_created,
            "credits_remaining": credits,
        },
    )
    db.add(event)
    db.commit()

    logger.info(
        f"SignalHire: searched {len(company_leads)} companies, "
        f"found {total_people_found} people, created {people_leads_created} leads"
    )
    return state
