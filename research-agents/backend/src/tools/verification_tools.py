"""Agno tool wrappers for verification skills."""

import json

from agno.tools import tool

from src.skills.verification.verify_entity import verify_entity
from src.skills.verification.verify_contact import verify_contact
from src.skills.verification.verify_source_quality import verify_source_quality
from src.skills.verification.dedup_resolver import check_duplicate
from src.models.lead import NormalizedLead


@tool
def verify_entity_tool(
    name: str,
    company_name: str = "",
    website: str = "",
    country: str = "",
    source_urls: str = "",
) -> str:
    """Verify whether a company or entity appears real and legitimate.

    Checks company registration plausibility, web presence, name consistency,
    and country-specific registry presence.

    Args:
        name: Person or entity name.
        company_name: Company name if different from name.
        website: Known website URL.
        country: Country for registry lookups.
        source_urls: Comma-separated list of URLs where entity was found.

    Returns:
        JSON verification result with score 0-1 and rationale.
    """
    result = verify_entity(
        name=name,
        company_name=company_name or None,
        website=website or None,
        country=country,
        source_urls=source_urls.split(",") if source_urls else None,
    )
    return json.dumps(result.model_dump(mode="json"))


@tool
def verify_contact_tool(
    email: str = "",
    phone: str = "",
    company_name: str = "",
    website: str = "",
    role_title: str = "",
    country: str = "",
) -> str:
    """Validate that contact information belongs to the claimed entity.

    Checks email domain vs company website, phone format for country,
    role/title plausibility, and contact presence on company web properties.

    Args:
        email: Email address to verify.
        phone: Phone number to verify.
        company_name: Company the contact claims to belong to.
        website: Known company website.
        role_title: Claimed role or title.
        country: Country for phone format validation.

    Returns:
        JSON verification result with score 0-1 and rationale.
    """
    result = verify_contact(
        email=email or None,
        phone=phone or None,
        company_name=company_name or None,
        website=website or None,
        role_title=role_title or None,
        country=country,
    )
    return json.dumps(result.model_dump(mode="json"))


@tool
def verify_source_quality_tool(
    source_urls: str = "",
    source_types: str = "",
    source_excerpts: str = "",
    source_count: int = 0,
) -> str:
    """Assess the strength and diversity of evidence supporting a lead.

    Checks source count, diversity of source types, domain reputation,
    and consistency across sources.

    Args:
        source_urls: Comma-separated URLs where the lead was found.
        source_types: Comma-separated types of each source (e.g. "news,directory,government").
        source_excerpts: Pipe-separated text excerpts from sources.
        source_count: Total number of sources if different from URL count.

    Returns:
        JSON verification result with score 0-1 and rationale.
    """
    result = verify_source_quality(
        source_urls=source_urls.split(",") if source_urls else None,
        source_types=source_types.split(",") if source_types else None,
        source_excerpts=source_excerpts.split("|") if source_excerpts else None,
        source_count=source_count,
    )
    return json.dumps(result.model_dump(mode="json"))


@tool
def check_duplicate_tool(
    candidate_json: str,
    existing_leads_json: str = "[]",
) -> str:
    """Check if a candidate lead is a duplicate of an existing one.

    Matching strategies: exact email, fuzzy company name, phone number,
    and website domain matching.

    Args:
        candidate_json: JSON string of the candidate NormalizedLead.
        existing_leads_json: JSON array of existing lead dicts with email, company_name, phone, website.

    Returns:
        JSON verification result with is_duplicate flag and duplicate_of_lead_id.
    """
    candidate = NormalizedLead.model_validate_json(candidate_json)
    existing = json.loads(existing_leads_json)
    result = check_duplicate(candidate=candidate, existing_leads=existing)
    return json.dumps(result.model_dump(mode="json"))
