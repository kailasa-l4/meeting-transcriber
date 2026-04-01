"""Broker Finder Agent -- discovers gold brokers and intermediaries."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.discovery_tools import search_brokers, extract_entity_contacts

broker_finder_agent = Agent(
    name="Broker Finder",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[search_brokers, extract_entity_contacts],
    role="Find gold brokers, intermediaries, and trading agents",
    description="Discovers gold brokers, intermediaries, agents, and trading contacts in target countries.",
    instructions=[
        "Search for gold brokers, intermediaries, and trading agents in the specified country.",
        "Include precious metals brokers, gold buyers, and middlemen.",
        "Look for brokers with established trade networks and verifiable identities.",
        "For each entity found, attempt to extract contact details.",
        "Return structured lead data with source URLs and broker specialization.",
        "Flag any entities that appear in multiple broker directories as higher-confidence leads.",
    ],
)
