"""Miner Finder Agent -- discovers gold mining companies and operators."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.discovery_tools import search_miners, extract_entity_contacts

miner_finder_agent = Agent(
    name="Miner Finder",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[search_miners, extract_entity_contacts],
    role="Find gold mining companies, operators, and artisanal miners",
    description="Discovers gold mining companies, operators, and artisanal miners in target countries.",
    instructions=[
        "Search for gold mining companies and operators in the specified country.",
        "Focus on companies with active mining operations and verifiable contact information.",
        "Include both large-scale and small-scale/artisanal miners.",
        "For each entity found, attempt to extract contact details.",
        "Return structured lead data with source URLs and company details.",
        "Prioritize entities with email addresses, phone numbers, and websites.",
    ],
)
