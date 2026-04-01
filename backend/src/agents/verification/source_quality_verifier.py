"""Source Quality Verifier Agent -- assesses evidence strength supporting a lead."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.verification_tools import verify_source_quality_tool

source_quality_verifier_agent = Agent(
    name="Source Quality Verifier",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[verify_source_quality_tool],
    role="Assess evidence strength from source count, diversity, and reputation",
    description="Evaluates the strength and diversity of evidence supporting each lead by analyzing source count, type diversity, and domain reputation.",
    instructions=[
        "For each lead, assess the quality and diversity of its supporting sources.",
        "Count the number of independent sources that mention the entity.",
        "Evaluate source diversity: government, news, directory, industry, social media, etc.",
        "Score domain reputation: government sites and established news outlets score highest.",
        "Check for consistency across sources (do they agree on company details?).",
        "Return a source quality score (0-1) with rationale.",
        "Leads with 3+ diverse, high-reputation sources should score above 0.7.",
    ],
)
