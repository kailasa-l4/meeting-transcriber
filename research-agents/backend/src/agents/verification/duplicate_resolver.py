"""Duplicate Resolver Agent -- detects and flags duplicate leads."""

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from src.config import settings
from src.tools.verification_tools import check_duplicate_tool
from src.tools.gws_tools import read_sheet_leads

duplicate_resolver_agent = Agent(
    name="Duplicate Resolver",
    model=OpenRouter(
        id="moonshotai/kimi-k2.5",
        api_key=settings.openrouter_api_key,
    ),
    tools=[check_duplicate_tool, read_sheet_leads],
    role="Detect and flag duplicate leads across the database and sheet",
    description="Checks new candidate leads against existing leads using email, company name, phone, and website matching to prevent duplicates.",
    instructions=[
        "For each candidate lead, check if it duplicates an existing lead.",
        "First read existing leads from the Google Sheet for comparison.",
        "Match by: exact email, normalized company name, phone number, and website domain.",
        "If a duplicate is found, flag it with the matching lead's ID and match type.",
        "If no duplicate is found, confirm the lead is unique.",
        "Fuzzy company name matching should normalize away suffixes like Ltd, Inc, Corp.",
        "Return clear duplicate/unique status with the matching field if duplicate.",
    ],
)
