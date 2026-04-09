"""Entity Verifier Agent -- checks if discovered entities are real and legitimate."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.verification_tools import verify_entity_tool

entity_verifier_agent = Agent(
    name="Entity Verifier",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[verify_entity_tool],
    role="Verify entity legitimacy through registration and web presence checks",
    description="Checks whether discovered companies and entities are real by verifying registration, web presence, and name pattern consistency.",
    instructions=[
        "For each entity, verify its legitimacy using available verification tools.",
        "Check company registration plausibility for the claimed country.",
        "Verify web presence: does the entity have a real website, social media, or directory listings?",
        "Look for name pattern consistency (e.g., suspicious generic names are lower confidence).",
        "Check country-specific business registries where possible.",
        "Return a verification score (0-1) with clear rationale for the assessment.",
        "Score above 0.7 indicates high confidence the entity is real.",
    ],
)
