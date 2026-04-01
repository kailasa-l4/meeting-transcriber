"""Contact Verifier Agent -- validates contact information belongs to claimed entities."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.verification_tools import verify_contact_tool

contact_verifier_agent = Agent(
    name="Contact Verifier",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[verify_contact_tool],
    role="Validate that contact details belong to the claimed entity",
    description="Validates email domains against company websites, phone format for country, role plausibility, and contact presence on company properties.",
    instructions=[
        "For each contact, verify that the information is consistent and belongs to the claimed entity.",
        "Check if the email domain matches the company website domain.",
        "Verify phone number format is plausible for the stated country.",
        "Assess whether the claimed role/title is plausible for the gold mining/trade sector.",
        "Check if the contact appears on the company's own web presence.",
        "Return a verification score (0-1) with detailed per-check breakdown.",
        "Generic email domains (gmail, yahoo, etc.) are not necessarily invalid but score lower.",
    ],
)
