"""Discovery skill for gold brokers and intermediaries."""
from src.models.lead import RawCandidate


def discover_brokers(
    country: str,
    regions: list[str] | None = None,
    known_entities: list[str] | None = None,
    existing_leads: list[str] | None = None,
) -> list[RawCandidate]:
    """Search for gold brokers, intermediaries, and trading contacts in a country.

    Args:
        country: Target country
        regions: Optional specific regions to focus on
        known_entities: Known brokers/agents to look for
        existing_leads: Emails/names of already-known leads (for dedup)

    Returns:
        List of raw candidate leads found
    """
    search_queries = _build_broker_queries(country, regions, known_entities)
    return []


def _build_broker_queries(
    country: str,
    regions: list[str] | None,
    known_entities: list[str] | None,
) -> list[str]:
    """Build search queries for broker/intermediary discovery."""
    base_queries = [
        f"gold broker {country}",
        f"gold agent {country}",
        f"gold intermediary {country}",
        f"gold trading company {country}",
        f"gold buyer {country} contact",
        f"gold middleman {country}",
        f"precious metals broker {country}",
    ]
    if regions:
        for region in regions:
            base_queries.extend([
                f"gold broker {region} {country}",
                f"gold agent {region} {country}",
            ])
    if known_entities:
        for entity in known_entities:
            base_queries.append(f"{entity} gold broker {country}")
    return base_queries


SKILL_METADATA = {
    "id": "discovery-brokers",
    "version": "1.0.0",
    "description": "Find gold brokers, intermediaries, and trading contacts",
    "primary_sources": ["trade directories", "business registries", "news", "forums"],
}
