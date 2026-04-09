"""Contact extraction skill."""
from src.models.lead import RawCandidate


def extract_contacts(
    entity_name: str,
    entity_url: str | None = None,
    country: str = "",
) -> RawCandidate:
    """Extract contact details for a discovered entity.

    Builds search queries to find email, phone, website, and key personnel
    for a given entity. The agent's web search tools execute the actual lookups.

    Args:
        entity_name: Company or person name
        entity_url: Known URL to scrape
        country: Country context

    Returns:
        RawCandidate with extracted contact information
    """
    search_queries = _build_contact_queries(entity_name, entity_url, country)
    return RawCandidate(
        name=entity_name,
        website=entity_url,
    )


def _build_contact_queries(
    entity_name: str,
    entity_url: str | None,
    country: str,
) -> list[str]:
    """Build search queries for contact extraction."""
    queries = [
        f"{entity_name} contact email",
        f"{entity_name} phone number",
        f"{entity_name} managing director",
        f"{entity_name} CEO",
    ]
    if country:
        queries.extend([
            f"{entity_name} {country} contact",
            f"{entity_name} {country} office address",
        ])
    if entity_url:
        queries.append(f"site:{entity_url} contact")
    return queries


SKILL_METADATA = {
    "id": "contact-extraction",
    "version": "1.0.0",
    "description": "Extract contact details from entities",
    "primary_sources": ["company websites", "directories", "public records"],
}
