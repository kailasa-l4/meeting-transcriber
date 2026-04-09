"""Source quality verification skill — assesses evidence strength."""
from src.models.verification import VerificationResult
from src.models.enums import VerificationDimension


def verify_source_quality(
    source_urls: list[str] | None = None,
    source_types: list[str] | None = None,
    source_excerpts: list[str] | None = None,
    source_count: int = 0,
) -> VerificationResult:
    """Assess the strength and diversity of evidence supporting a lead.

    Checks:
    - Source count (more independent sources = higher confidence)
    - Source diversity (different types of sources)
    - Source domain reputation (government, news, directory, etc.)
    - Consistency across sources

    Args:
        source_urls: URLs where the lead was found
        source_types: Types of each source (e.g. "news", "directory", "government")
        source_excerpts: Relevant text excerpts from sources
        source_count: Total number of sources

    Returns:
        VerificationResult with score 0-1 and rationale
    """
    checks: list[str] = []
    score = 0.0

    urls = source_urls or []
    types = source_types or []
    effective_count = max(source_count, len(urls))

    # Source count scoring
    if effective_count == 0:
        score = 0.1
        checks.append("No sources provided")
    elif effective_count == 1:
        score = 0.3
        checks.append("Single source only")
    elif effective_count == 2:
        score = 0.5
        checks.append("Two sources found")
    elif effective_count >= 3:
        score = 0.7
        checks.append(f"{effective_count} sources found")

    # Source diversity bonus
    if types:
        unique_types = set(types)
        if len(unique_types) >= 3:
            score += 0.15
            checks.append(f"High diversity: {len(unique_types)} source types")
        elif len(unique_types) == 2:
            score += 0.1
            checks.append(f"Moderate diversity: {len(unique_types)} source types")

    # Domain reputation scoring
    if urls:
        high_rep_count = sum(1 for u in urls if _is_high_reputation_domain(u))
        if high_rep_count > 0:
            score += 0.1
            checks.append(f"{high_rep_count} high-reputation source(s)")

    # Clamp score
    score = max(0.0, min(1.0, score))

    rationale = "; ".join(checks) if checks else "No sources to evaluate"
    return VerificationResult(
        dimension=VerificationDimension.source_quality,
        score=score,
        rationale=rationale,
        skill_used="verify-source-quality",
    )


# Domains considered high-reputation for mining/trade leads
_HIGH_REPUTATION_DOMAINS = {
    ".gov", ".go.", ".mil",           # Government
    "reuters.com", "bloomberg.com",   # Wire services
    "mining.com", "miningweekly.com", # Mining industry
    "linkedin.com",                   # Professional network
    "chamberofmines",                 # Industry chambers
    "mineralcommission",              # Regulators
}


def _is_high_reputation_domain(url: str) -> bool:
    """Check if a URL is from a high-reputation domain."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in _HIGH_REPUTATION_DOMAINS)


SKILL_METADATA = {
    "id": "verify-source-quality",
    "version": "1.0.0",
    "description": "Assess evidence strength from source count, diversity, and reputation",
    "output": "Score 0-1 + rationale with per-check breakdown",
}
