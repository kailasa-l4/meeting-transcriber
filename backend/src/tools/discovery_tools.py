"""Agno tool wrappers for discovery skills."""

import json

from agno.tools import tool

from src.skills.discovery.discovery_miners import discover_miners
from src.skills.discovery.discovery_brokers import discover_brokers
from src.skills.discovery.discovery_exporters import discover_exporters
from src.skills.discovery.discovery_directories import discover_directories
from src.skills.discovery.contact_extraction import extract_contacts


@tool
def search_miners(country: str, regions: str = "", known_entities: str = "", existing_leads: str = "") -> str:
    """Search for gold mining companies and operators in a country.

    Args:
        country: Target country (e.g. "Kenya", "Ghana", "Uganda", "Nigeria").
        regions: Comma-separated list of regions to focus on.
        known_entities: Comma-separated list of known company names to look for.
        existing_leads: Comma-separated list of already-known lead emails/names for dedup.

    Returns:
        JSON array of raw candidate leads found.
    """
    results = discover_miners(
        country=country,
        regions=regions.split(",") if regions else None,
        known_entities=known_entities.split(",") if known_entities else None,
        existing_leads=existing_leads.split(",") if existing_leads else None,
    )
    return json.dumps([r.model_dump() for r in results])


@tool
def search_brokers(country: str, regions: str = "", known_entities: str = "", existing_leads: str = "") -> str:
    """Search for gold brokers, intermediaries, and trading contacts in a country.

    Args:
        country: Target country (e.g. "Kenya", "Ghana", "Uganda", "Nigeria").
        regions: Comma-separated list of regions to focus on.
        known_entities: Comma-separated list of known broker names to look for.
        existing_leads: Comma-separated list of already-known lead emails/names for dedup.

    Returns:
        JSON array of raw candidate leads found.
    """
    results = discover_brokers(
        country=country,
        regions=regions.split(",") if regions else None,
        known_entities=known_entities.split(",") if known_entities else None,
        existing_leads=existing_leads.split(",") if existing_leads else None,
    )
    return json.dumps([r.model_dump() for r in results])


@tool
def search_exporters(country: str, regions: str = "", known_entities: str = "", existing_leads: str = "") -> str:
    """Search for gold exporters, traders, and precious metals dealers in a country.

    Args:
        country: Target country (e.g. "Kenya", "Ghana", "Uganda", "Nigeria").
        regions: Comma-separated list of regions to focus on.
        known_entities: Comma-separated list of known exporter names to look for.
        existing_leads: Comma-separated list of already-known lead emails/names for dedup.

    Returns:
        JSON array of raw candidate leads found.
    """
    results = discover_exporters(
        country=country,
        regions=regions.split(",") if regions else None,
        known_entities=known_entities.split(",") if known_entities else None,
        existing_leads=existing_leads.split(",") if existing_leads else None,
    )
    return json.dumps([r.model_dump() for r in results])


@tool
def search_directories(country: str, regions: str = "", known_entities: str = "", existing_leads: str = "") -> str:
    """Search for mining directories, associations, chambers, and registries in a country.

    These are meta-sources that list or govern mining companies, providing bulk discovery.

    Args:
        country: Target country (e.g. "Kenya", "Ghana", "Uganda", "Nigeria").
        regions: Comma-separated list of regions to focus on.
        known_entities: Comma-separated list of known association names to look for.
        existing_leads: Comma-separated list of already-known lead emails/names for dedup.

    Returns:
        JSON array of raw candidate leads found.
    """
    results = discover_directories(
        country=country,
        regions=regions.split(",") if regions else None,
        known_entities=known_entities.split(",") if known_entities else None,
        existing_leads=existing_leads.split(",") if existing_leads else None,
    )
    return json.dumps([r.model_dump() for r in results])


@tool
def extract_entity_contacts(entity_name: str, entity_url: str = "", country: str = "") -> str:
    """Extract contact details (email, phone, personnel) for a discovered entity.

    Args:
        entity_name: Company or person name to look up.
        entity_url: Known URL to scrape for contacts.
        country: Country context for the search.

    Returns:
        JSON object with extracted contact information.
    """
    result = extract_contacts(
        entity_name=entity_name,
        entity_url=entity_url or None,
        country=country,
    )
    return json.dumps(result.model_dump())
