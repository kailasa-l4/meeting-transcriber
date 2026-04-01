"""Verification Team -- validates and scores discovered leads across all dimensions."""

from agno.models.openrouter import OpenRouter
from agno.team.mode import TeamMode
from agno.team.team import Team

from src.config import settings
from src.agents.verification.entity_verifier import entity_verifier_agent
from src.agents.verification.contact_verifier import contact_verifier_agent
from src.agents.verification.source_quality_verifier import source_quality_verifier_agent
from src.agents.verification.duplicate_resolver import duplicate_resolver_agent

verification_team = Team(
    name="Verification Team",
    mode=TeamMode.coordinate,
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    members=[
        entity_verifier_agent,
        contact_verifier_agent,
        source_quality_verifier_agent,
        duplicate_resolver_agent,
    ],
    instructions=[
        "You lead a team that verifies discovered leads across all quality dimensions.",
        "For each lead, coordinate verification across all team members:",
        "  - Entity Verifier: confirm the company/entity is real and registered.",
        "  - Contact Verifier: validate email, phone, and role belong to the entity.",
        "  - Source Quality Verifier: assess the strength and diversity of evidence.",
        "  - Duplicate Resolver: check against existing leads for duplicates.",
        "Produce a final confidence score by combining dimension scores.",
        "Leads scoring above 0.7 overall should be marked as verified.",
        "Leads scoring 0.4-0.7 should be marked as needs_review.",
        "Leads scoring below 0.4 should be flagged for rejection.",
        "Always include the rationale for each dimension in the final assessment.",
    ],
    show_members_responses=True,
    markdown=True,
)
