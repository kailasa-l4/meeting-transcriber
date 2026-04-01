"""Deduplication resolver skill."""
from src.models.verification import VerificationResult
from src.models.enums import VerificationDimension
from src.models.lead import NormalizedLead


def check_duplicate(
    candidate: NormalizedLead,
    existing_leads: list[dict],
) -> VerificationResult:
    """Check if a candidate lead is a duplicate of an existing one.

    Matching strategies:
    - Exact email match
    - Fuzzy company name match (normalized)
    - Phone number match (after normalization)
    - Website domain match

    Args:
        candidate: The lead to check
        existing_leads: List of existing lead dicts with email, company_name, phone, website

    Returns:
        VerificationResult with is_duplicate flag and duplicate_of_lead_id
    """
    for existing in existing_leads:
        # Exact email match
        if candidate.email and existing.get("email"):
            if candidate.email.lower().strip() == existing["email"].lower().strip():
                return VerificationResult(
                    dimension=VerificationDimension.dedup,
                    score=1.0,
                    rationale=f"Exact email match: {candidate.email}",
                    is_duplicate=True,
                    duplicate_of_lead_id=existing.get("id"),
                    skill_used="dedup-resolver",
                )

        # Normalized company name match
        if candidate.company_name and existing.get("company_name"):
            if _normalize_company(candidate.company_name) == _normalize_company(
                existing["company_name"]
            ):
                return VerificationResult(
                    dimension=VerificationDimension.dedup,
                    score=0.9,
                    rationale=f"Company name match: {candidate.company_name}",
                    is_duplicate=True,
                    duplicate_of_lead_id=existing.get("id"),
                    skill_used="dedup-resolver",
                )

        # Phone number match (after stripping formatting)
        if candidate.phone and existing.get("phone"):
            if _normalize_phone(candidate.phone) == _normalize_phone(existing["phone"]):
                return VerificationResult(
                    dimension=VerificationDimension.dedup,
                    score=0.85,
                    rationale=f"Phone match: {candidate.phone}",
                    is_duplicate=True,
                    duplicate_of_lead_id=existing.get("id"),
                    skill_used="dedup-resolver",
                )

        # Website domain match
        if candidate.website and existing.get("website"):
            if _extract_domain(candidate.website) == _extract_domain(existing["website"]):
                return VerificationResult(
                    dimension=VerificationDimension.dedup,
                    score=0.8,
                    rationale=f"Website domain match: {candidate.website}",
                    is_duplicate=True,
                    duplicate_of_lead_id=existing.get("id"),
                    skill_used="dedup-resolver",
                )

    return VerificationResult(
        dimension=VerificationDimension.dedup,
        score=1.0,
        rationale="No duplicate found",
        is_duplicate=False,
        skill_used="dedup-resolver",
    )


def _normalize_company(name: str) -> str:
    """Normalize company name for comparison."""
    name = name.lower().strip()
    for suffix in [" ltd", " limited", " inc", " corp", " co", " plc", " llc", " gmbh"]:
        name = name.removesuffix(suffix)
    return name.strip()


def _normalize_phone(phone: str) -> str:
    """Strip all formatting from phone number for comparison."""
    return "".join(c for c in phone if c.isdigit() or c == "+")


def _extract_domain(url: str) -> str:
    """Extract bare domain from URL for comparison."""
    url = url.lower().strip()
    for prefix in ["https://", "http://", "www."]:
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url.split("/", 1)[0].strip()


SKILL_METADATA = {
    "id": "dedup-resolver",
    "version": "1.0.0",
    "description": "Detect and merge duplicates",
    "output": "Duplicate flag + canonical ID",
}
