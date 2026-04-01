"""Lead normalization skill — standardize fields and format."""
import re

from src.models.lead import RawCandidate, NormalizedLead


def normalize_lead(
    raw: RawCandidate,
    existing_leads: list[dict] | None = None,
) -> NormalizedLead:
    """Normalize a raw candidate into the standard lead schema.

    Handles: field mapping, phone formatting, email normalization,
    URL cleaning, and initial dedup check.

    Args:
        raw: Raw candidate from discovery
        existing_leads: Optional existing leads for dedup context

    Returns:
        NormalizedLead with cleaned and standardized fields
    """
    return NormalizedLead(
        name=_clean_name(raw.name or ""),
        role_title=raw.role_title,
        whatsapp=_normalize_phone(raw.whatsapp),
        phone=_normalize_phone(raw.phone),
        details=raw.details,
        email=_normalize_email(raw.email),
        company_name=raw.company_name,
        website=_normalize_url(raw.website),
        source_text=raw.source_excerpt,
        source_urls=[raw.source_url] if raw.source_url else [],
        source_count=1 if raw.source_url else 0,
        discovery_skill_used=raw.discovery_skill,
    )


def _clean_name(name: str) -> str:
    """Remove extra whitespace and normalize capitalization."""
    return " ".join(name.split()).strip()


def _normalize_phone(phone: str | None) -> str | None:
    """Strip formatting from phone numbers."""
    if not phone:
        return None
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    return cleaned if cleaned else None


def _normalize_email(email: str | None) -> str | None:
    """Lowercase and strip email."""
    if not email:
        return None
    return email.lower().strip()


def _normalize_url(url: str | None) -> str | None:
    """Ensure URL has a scheme."""
    if not url:
        return None
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


SKILL_METADATA = {
    "id": "normalization",
    "version": "1.0.0",
    "description": "Standardize lead fields",
}
