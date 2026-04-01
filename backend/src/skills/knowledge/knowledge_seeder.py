"""Knowledge seeder skill — load country domain knowledge."""
from sqlalchemy.orm import Session

from src.db.models import CountryKnowledge


def load_country_knowledge(country: str, db: Session) -> list[dict]:
    """Load all domain knowledge for a country.

    Returns structured knowledge entries that agents use to
    seed their research context.

    Args:
        country: Country to load knowledge for
        db: SQLAlchemy session

    Returns:
        List of knowledge entry dicts with type, content, source
    """
    entries = db.query(CountryKnowledge).filter(
        CountryKnowledge.country == country
    ).all()

    return [
        {
            "type": entry.knowledge_type.value if entry.knowledge_type else None,
            "content": entry.content,
            "source": entry.source,
        }
        for entry in entries
    ]


def seed_default_knowledge(country: str) -> dict:
    """Generate default research context for a country with no prior knowledge.

    Returns a research plan template that discovery agents can use.

    Args:
        country: Target country

    Returns:
        Dict with country, search strategies, expected lead types, and regulatory hints
    """
    return {
        "country": country,
        "search_strategies": [
            f"gold mining companies in {country}",
            f"gold trade associations {country}",
            f"mining chamber {country}",
            f"gold export {country}",
            f"precious metals dealers {country}",
        ],
        "expected_lead_types": [
            "miners",
            "brokers",
            "exporters",
            "refiners",
            "associations",
        ],
        "regulatory_hint": f"Check {country} mining ministry and mineral commission websites",
    }


SKILL_METADATA = {
    "id": "knowledge-seeder",
    "version": "1.0.0",
    "description": "Load and seed country domain knowledge",
}
