"""Contact Extractor Agent -- extracts detailed contact information for discovered entities."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.discovery_tools import extract_entity_contacts

contact_extractor_agent = Agent(
    name="Contact Extractor",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[extract_entity_contacts],
    role="Extract and enrich contact details for discovered entities",
    description="Extracts email addresses, phone numbers, WhatsApp contacts, key personnel names, and titles for entities found by other discovery agents.",
    instructions=[
        "For each entity provided, extract the most complete contact information possible.",
        "Prioritize finding: email, phone/WhatsApp, key person name, and role/title.",
        "Check the entity's website, LinkedIn presence, and directory listings.",
        "If multiple contacts are found, prefer the most senior decision-maker.",
        "Return structured contact data with the source URL for each piece of information.",
        "Flag contacts found on the entity's own domain as higher confidence.",
    ],
)
