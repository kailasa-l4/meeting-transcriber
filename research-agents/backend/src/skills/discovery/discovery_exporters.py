"""Discovery skill for gold exporters and precious metals dealers."""
from src.models.lead import RawCandidate


def discover_exporters(
    country: str,
    regions: list[str] | None = None,
    known_entities: list[str] | None = None,
    existing_leads: list[str] | None = None,
) -> list[RawCandidate]:
    """Search for gold exporters, traders, and precious metals dealers in a country.

    Args:
        country: Target country
        regions: Optional specific regions to focus on
        known_entities: Known exporters/dealers to look for
        existing_leads: Emails/names of already-known leads (for dedup)

    Returns:
        List of raw candidate leads found
    """
    search_queries = _build_exporter_queries(country, regions, known_entities)
    return []


def _build_exporter_queries(
    country: str,
    regions: list[str] | None,
    known_entities: list[str] | None,
) -> list[str]:
    """Build search queries for exporter/dealer discovery."""
    base_queries = [
        f"gold exporter {country}",
        f"gold trader {country}",
        f"precious metals dealer {country}",
        f"gold export company {country}",
        f"gold refinery {country}",
        f"gold dealer {country} contact",
        f"licensed gold exporter {country}",
        f"gold export license {country}",
    ]
    if regions:
        for region in regions:
            base_queries.extend([
                f"gold exporter {region} {country}",
                f"precious metals dealer {region} {country}",
            ])
    if known_entities:
        for entity in known_entities:
            base_queries.append(f"{entity} gold export {country}")
    return base_queries


SKILL_METADATA = {
    "id": "discovery-exporters",
    "version": "1.0.0",
    "description": "Find gold exporters, traders, and precious metals dealers",
    "primary_sources": ["export registries", "trade databases", "customs records", "news"],
}
