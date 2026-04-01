"""Discovery skill for mining companies and operators."""
from src.models.lead import RawCandidate


def discover_miners(
    country: str,
    regions: list[str] | None = None,
    known_entities: list[str] | None = None,
    existing_leads: list[str] | None = None,
) -> list[RawCandidate]:
    """Search for gold mining companies and operators in a country.

    Args:
        country: Target country
        regions: Optional specific regions to focus on
        known_entities: Known companies to look for
        existing_leads: Emails/names of already-known leads (for dedup)

    Returns:
        List of raw candidate leads found
    """
    # This is the skill interface — actual implementation will use
    # web search tools provided by the agent at runtime.
    # The skill defines the search strategy and extraction patterns.
    search_queries = _build_miner_queries(country, regions, known_entities)
    return []


def _build_miner_queries(
    country: str,
    regions: list[str] | None,
    known_entities: list[str] | None,
) -> list[str]:
    """Build search queries for mining company discovery."""
    base_queries = [
        f"gold mining companies {country}",
        f"gold miners {country} contact",
        f"gold mining operators {country}",
        f"alluvial gold mining {country}",
        f"small scale gold mining {country}",
    ]
    if regions:
        for region in regions:
            base_queries.extend([
                f"gold mining companies {region} {country}",
                f"gold miners {region}",
            ])
    if known_entities:
        for entity in known_entities:
            base_queries.append(f"{entity} gold mining {country}")
    return base_queries


SKILL_METADATA = {
    "id": "discovery-miners",
    "version": "1.0.0",
    "description": "Find gold mining companies and operators",
    "primary_sources": ["company registries", "mining directories", "news"],
}
