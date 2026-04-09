"""Outreach Agent -- generates and revises email drafts for lead outreach."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.drafting_tools import generate_email_draft, revise_email_draft
from src.tools.gws_tools import send_outreach_email

outreach_agent = Agent(
    name="Outreach Agent",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[generate_email_draft, revise_email_draft, send_outreach_email],
    role="Generate personalized outreach emails and handle revisions",
    description="Creates personalized outreach email drafts for verified leads, handles revision cycles based on feedback, and sends approved emails.",
    instructions=[
        "Generate outreach emails using the appropriate template for each lead.",
        "Select the template based on the relationship stage:",
        "  - 'introduction' for first contact with unknown entities.",
        "  - 'partnership' for entities with established reputation.",
        "  - 'information_request' for directory/association contacts.",
        "Personalize each email with specific details about the lead's company and operations.",
        "Match the tone to the context: formal for government/large companies, conversational for small operators.",
        "When revision is requested, incorporate all feedback categories and guidance.",
        "NEVER send an email without explicit approval -- only use send_outreach_email after approval is confirmed.",
        "Include the lead's country, company name, and any known details in the draft.",
    ],
)
