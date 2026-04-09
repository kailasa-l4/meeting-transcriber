"""Entity verification skill — checks if an entity appears real."""
from src.models.verification import VerificationResult
from src.models.enums import VerificationDimension


def verify_entity(
    name: str,
    company_name: str | None = None,
    website: str | None = None,
    country: str = "",
    source_urls: list[str] | None = None,
) -> VerificationResult:
    """Check whether a company/person/entity appears real and legitimate.

    Checks: company registration plausibility, web presence,
    name pattern consistency, country-specific registry presence.

    Args:
        name: Person or entity name
        company_name: Company name if different from name
        website: Known website URL
        country: Country for registry lookups
        source_urls: URLs where entity was found

    Returns:
        VerificationResult with score 0-1 and rationale
    """
    # Placeholder — real implementation uses the agent's web search tools
    return VerificationResult(
        dimension=VerificationDimension.entity,
        score=0.5,
        rationale="Pending verification",
        skill_used="verify-entity",
    )


def _build_entity_check_queries(
    name: str,
    company_name: str | None,
    country: str,
) -> list[str]:
    """Build queries to verify entity legitimacy."""
    target = company_name or name
    queries = [
        f'"{target}" company registration',
        f'"{target}" official website',
        f'"{target}" gold mining',
    ]
    if country:
        queries.extend([
            f'"{target}" {country} registered company',
            f'"{target}" {country} mining license',
            f'{country} company registry "{target}"',
        ])
    return queries


SKILL_METADATA = {
    "id": "verify-entity",
    "version": "1.0.0",
    "description": "Check entity plausibility",
    "output": "Score 0-1 + rationale",
}
