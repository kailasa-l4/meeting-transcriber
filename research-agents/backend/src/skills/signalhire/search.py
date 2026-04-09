"""SignalHire Search API skill — find real people at companies (FREE, no credits)."""

import logging
import httpx

from src.config import settings

logger = logging.getLogger(__name__)

SIGNALHIRE_BASE = "https://www.signalhire.com/api/v1"


def search_people(
    company: str,
    location: str = "",
    title: str = "",
    industry: str = "Mining & Metals",
    keywords: str = "gold",
    size: int = 10,
) -> list[dict]:
    """Search SignalHire for people at a company/location.

    This uses the Search API which is FREE (no credits consumed).
    Returns profile overviews without contact details.

    Args:
        company: Company name to search
        location: Country or city
        title: Job title filter (supports Boolean: "CEO" OR "Director")
        industry: Industry filter
        keywords: Skill/bio keywords
        size: Max results (1-100)

    Returns:
        List of profile dicts with name, headline, location, company, uid
    """
    if not settings.signalhire_api_key:
        logger.warning("SignalHire API key not configured, skipping search")
        return []

    body = {
        "size": min(size, 100),
        "company": company,
        "industry": industry,
    }
    if location:
        body["location"] = location
    if title:
        body["title"] = title
    if keywords:
        body["keywords"] = keywords

    try:
        resp = httpx.post(
            f"{SIGNALHIRE_BASE}/candidate/searchByQuery",
            headers={"apikey": settings.signalhire_api_key, "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )

        if resp.status_code == 401:
            logger.error("SignalHire: authentication failed (401)")
            return []
        if resp.status_code == 429:
            logger.warning("SignalHire: rate limited (429)")
            return []
        if resp.status_code != 200:
            logger.warning(f"SignalHire search returned {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()
        profiles = data.get("profiles", [])
        total = data.get("total", 0)
        logger.info(f"SignalHire: found {total} results for '{company}' in '{location}' (returned {len(profiles)})")

        return [_normalize_profile(p) for p in profiles]

    except httpx.TimeoutException:
        logger.warning(f"SignalHire: timeout searching for '{company}'")
        return []
    except Exception as exc:
        logger.error(f"SignalHire search error: {exc}")
        return []


def _normalize_profile(profile: dict) -> dict:
    """Extract useful fields from a SignalHire search result profile."""
    # Profile structure varies — handle both formats
    experience = profile.get("experience", [])
    current_job = next((e for e in experience if e.get("current")), experience[0] if experience else {})

    return {
        "uid": profile.get("uid", ""),
        "name": profile.get("fullName", ""),
        "headline": profile.get("headLine", ""),
        "role_title": current_job.get("position", profile.get("headLine", "")),
        "company_name": current_job.get("company", ""),
        "company_website": current_job.get("website", ""),
        "industry": current_job.get("industry", ""),
        "location": _get_location(profile),
        "linkedin_url": _get_social(profile, "li"),
        "source": "signalhire_search",
    }


def _get_location(profile: dict) -> str:
    """Extract location string from profile."""
    locations = profile.get("locations", [])
    if locations:
        return locations[0].get("name", "") if isinstance(locations[0], dict) else str(locations[0])
    return ""


def _get_social(profile: dict, social_type: str) -> str:
    """Extract a social link from profile."""
    for s in profile.get("social", []):
        if s.get("type") == social_type:
            return s.get("link", "")
    return ""


def check_credits() -> int:
    """Check remaining SignalHire credits."""
    if not settings.signalhire_api_key:
        return 0
    try:
        resp = httpx.get(
            f"{SIGNALHIRE_BASE}/credits",
            headers={"apikey": settings.signalhire_api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("credits", 0)
    except Exception:
        pass
    return -1


SKILL_METADATA = {
    "id": "signalhire-search",
    "version": "1.0.0",
    "description": "Search SignalHire for people at companies (free, no credits)",
}
