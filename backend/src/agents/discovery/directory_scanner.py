"""Directory Scanner Agent -- discovers mining associations, registries, and directories."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.discovery_tools import search_directories, extract_entity_contacts

directory_scanner_agent = Agent(
    name="Directory Scanner",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[search_directories, extract_entity_contacts],
    role="Find mining directories, associations, chambers, and government registries",
    description="Discovers meta-sources: mining associations, chambers of mines, government registries, and industry directories that list mining companies.",
    instructions=[
        "Search for mining directories, associations, and government registries in the specified country.",
        "These are meta-sources that list or govern mining companies, providing bulk discovery opportunities.",
        "Look for chambers of mines, minerals commissions, mining ministries, and artisanal miner cooperatives.",
        "For each directory/association found, extract contact details for the organization itself.",
        "Note the number of member companies listed where possible.",
        "Government and regulatory sources are highest priority.",
    ],
)
