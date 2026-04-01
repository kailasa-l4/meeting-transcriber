"""Exporter Finder Agent -- discovers gold exporters and precious metals dealers."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.discovery_tools import search_exporters, extract_entity_contacts

exporter_finder_agent = Agent(
    name="Exporter Finder",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[search_exporters, extract_entity_contacts],
    role="Find gold exporters, traders, and precious metals dealers",
    description="Discovers gold exporters, traders, refineries, and licensed precious metals dealers in target countries.",
    instructions=[
        "Search for gold exporters, traders, and precious metals dealers in the specified country.",
        "Prioritize licensed exporters and those with export permits.",
        "Include gold refineries and assay offices that handle export-grade gold.",
        "For each entity found, attempt to extract contact details.",
        "Return structured lead data with source URLs, export license info if available.",
        "Note any regulatory body references (minerals commission, export authority) as high-value sources.",
    ],
)
