"""Discovery Team -- coordinates parallel lead discovery across multiple categories."""

from agno.models.openrouter import OpenRouter
from agno.team.mode import TeamMode
from agno.team.team import Team

from src.config import settings
from src.agents.discovery.miner_finder import miner_finder_agent
from src.agents.discovery.broker_finder import broker_finder_agent
from src.agents.discovery.exporter_finder import exporter_finder_agent
from src.agents.discovery.directory_scanner import directory_scanner_agent
from src.agents.discovery.contact_extractor import contact_extractor_agent

discovery_team = Team(
    name="Discovery Team",
    mode=TeamMode.coordinate,
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    members=[
        miner_finder_agent,
        broker_finder_agent,
        exporter_finder_agent,
        directory_scanner_agent,
        contact_extractor_agent,
    ],
    instructions=[
        "You lead a team that discovers gold-related leads across multiple categories.",
        "For each country request, fan out to all discovery agents in parallel:",
        "  - Miner Finder: gold mining companies and operators.",
        "  - Broker Finder: gold brokers, intermediaries, and agents.",
        "  - Exporter Finder: gold exporters, traders, and dealers.",
        "  - Directory Scanner: mining associations, registries, and directories.",
        "After initial discovery, use the Contact Extractor to enrich any entities missing contact details.",
        "Consolidate all results and remove obvious duplicates before returning.",
        "Prioritize leads with verifiable contact information (email, phone, website).",
    ],
    show_members_responses=True,
    markdown=True,
)
