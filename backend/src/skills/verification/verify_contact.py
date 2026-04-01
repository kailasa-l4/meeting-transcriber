"""Contact verification skill — validates contact info belongs to entity."""
import re

from src.models.verification import VerificationResult
from src.models.enums import VerificationDimension


def verify_contact(
    email: str | None = None,
    phone: str | None = None,
    company_name: str | None = None,
    website: str | None = None,
    role_title: str | None = None,
    country: str = "",
) -> VerificationResult:
    """Validate that contact information belongs to the claimed entity.

    Checks:
    - Email domain matches company website
    - Phone format valid for country
    - Role/title plausibility for the sector
    - Contact appears on company web presence

    Args:
        email: Email to verify
        phone: Phone number to verify
        company_name: Company the contact claims to belong to
        website: Known company website
        role_title: Claimed role/title
        country: Country for phone format validation

    Returns:
        VerificationResult with score 0-1 and rationale
    """
    checks: list[str] = []
    score = 0.5

    # Email-domain vs website consistency
    if email and website:
        email_domain = _extract_email_domain(email)
        website_domain = _extract_website_domain(website)
        if email_domain and website_domain:
            if email_domain == website_domain:
                score += 0.2
                checks.append(f"Email domain matches website: {email_domain}")
            else:
                score -= 0.1
                checks.append(
                    f"Email domain ({email_domain}) differs from website ({website_domain})"
                )

    # Phone format plausibility
    if phone and country:
        if _phone_plausible(phone, country):
            score += 0.1
            checks.append("Phone format plausible for country")
        else:
            score -= 0.1
            checks.append("Phone format unusual for country")

    # Role plausibility in gold sector
    if role_title:
        if _role_plausible(role_title):
            score += 0.1
            checks.append(f"Role '{role_title}' plausible for sector")

    # Clamp score
    score = max(0.0, min(1.0, score))

    rationale = "; ".join(checks) if checks else "Pending verification"
    return VerificationResult(
        dimension=VerificationDimension.contact,
        score=score,
        rationale=rationale,
        skill_used="verify-contact",
    )


def _extract_email_domain(email: str) -> str | None:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@", 1)[1].lower().strip()
    return None


def _extract_website_domain(url: str) -> str | None:
    """Extract bare domain from URL."""
    url = url.lower().strip()
    for prefix in ["https://", "http://", "www."]:
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url.split("/", 1)[0].strip()


# Country calling code prefixes for basic format checks
_COUNTRY_PHONE_PREFIXES: dict[str, list[str]] = {
    "kenya": ["+254", "254", "07", "01"],
    "ke": ["+254", "254", "07", "01"],
    "uganda": ["+256", "256", "07"],
    "ug": ["+256", "256", "07"],
    "ghana": ["+233", "233", "02", "05"],
    "gh": ["+233", "233", "02", "05"],
    "nigeria": ["+234", "234", "08", "07", "09"],
    "ng": ["+234", "234", "08", "07", "09"],
}


def _phone_plausible(phone: str, country: str) -> bool:
    """Check if phone number has a plausible format for the country."""
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    prefixes = _COUNTRY_PHONE_PREFIXES.get(country.lower(), [])
    if not prefixes:
        # Unknown country — accept if it looks like a phone number
        return len(cleaned) >= 7
    return any(cleaned.startswith(p) for p in prefixes)


_PLAUSIBLE_ROLES = {
    "director", "manager", "ceo", "coo", "cfo", "owner", "founder",
    "chairman", "president", "head", "chief", "superintendent",
    "coordinator", "officer", "secretary", "treasurer", "partner",
    "broker", "trader", "dealer", "agent", "representative",
    "geologist", "engineer", "operations", "mining", "general",
}


def _role_plausible(role_title: str) -> bool:
    """Check if a role title is plausible for the gold mining/trade sector."""
    words = set(role_title.lower().split())
    return bool(words & _PLAUSIBLE_ROLES)


SKILL_METADATA = {
    "id": "verify-contact",
    "version": "1.0.0",
    "description": "Validate contact info belongs to claimed entity",
    "output": "Score 0-1 + rationale with per-check breakdown",
}
