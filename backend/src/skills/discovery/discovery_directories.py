"""Discovery skill for mining directories, associations, and registries."""
from src.models.lead import RawCandidate


def discover_directories(
    country: str,
    regions: list[str] | None = None,
    known_entities: list[str] | None = None,
    existing_leads: list[str] | None = None,
) -> list[RawCandidate]:
    """Search for mining directories, chambers, associations, and registries in a country.

    These are meta-sources: organizations that list or govern mining companies,
    providing bulk discovery opportunities.

    Args:
        country: Target country
        regions: Optional specific regions to focus on
        known_entities: Known associations/directories to look for
        existing_leads: Emails/names of already-known leads (for dedup)

    Returns:
        List of raw candidate leads found
    """
    search_queries = _build_directory_queries(country, regions, known_entities)
    return []


def _build_directory_queries(
    country: str,
    regions: list[str] | None,
    known_entities: list[str] | None,
) -> list[str]:
    """Build search queries for directory/association discovery."""
    base_queries = [
        f"mining association {country}",
        f"chamber of mines {country}",
        f"gold mining registry {country}",
        f"mining directory {country}",
        f"minerals commission {country}",
        f"mining ministry {country}",
        f"gold miners association {country}",
        f"artisanal mining association {country}",
        f"small scale miners organization {country}",
    ]
    if regions:
        for region in regions:
            base_queries.extend([
                f"mining association {region} {country}",
                f"miners cooperative {region} {country}",
            ])
    if known_entities:
        for entity in known_entities:
            base_queries.append(f"{entity} mining directory {country}")
    return base_queries


SKILL_METADATA = {
    "id": "discovery-directories",
    "version": "1.0.0",
    "description": "Find mining directories, chambers, associations, and registries",
    "primary_sources": ["government sites", "industry associations", "international bodies"],
}
