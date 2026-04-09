"""Agno tool wrappers for draft generation and revision skills."""

import json

from agno.tools import tool

from src.skills.drafting.draft_generation import generate_draft, revise_draft
from src.models.email_draft import DraftGenerationInput


@tool
def generate_email_draft(
    lead_name: str,
    country: str,
    company_name: str = "",
    lead_details: str = "",
    outreach_tone: str = "formal",
    template_family: str = "introduction",
    language: str = "en",
) -> str:
    """Generate an outreach email draft from a template for a specific lead.

    Available templates: introduction, partnership, information_request.
    Available tones: formal, conversational, partnership.

    Args:
        lead_name: The lead's name for the greeting.
        country: Target country.
        company_name: Company name for personalization.
        lead_details: Additional details about the lead for personalization.
        outreach_tone: Desired tone (formal, conversational, partnership).
        template_family: Template to use (introduction, partnership, information_request).
        language: Language code (default "en").

    Returns:
        JSON object with subject, body, and template_used.
    """
    input_data = DraftGenerationInput(
        lead_name=lead_name,
        company_name=company_name or None,
        country=country,
        lead_details=lead_details or None,
        outreach_tone=outreach_tone,
        template_family=template_family,
        language=language,
    )
    result = generate_draft(input_data)
    return json.dumps(result)


@tool
def revise_email_draft(
    original_subject: str,
    original_body: str,
    feedback_categories: str = "",
    comments: str = "",
    guidance: str = "",
) -> str:
    """Revise an outreach email draft based on structured feedback.

    Args:
        original_subject: Current draft subject line.
        original_body: Current draft body text.
        feedback_categories: Comma-separated feedback categories
            (tone_adjustment, missing_information, factual_error, length_issue,
             wrong_template, personalization_needed, other).
        comments: Free-form reviewer comments.
        guidance: Specific guidance for how to revise.

    Returns:
        JSON object with revised subject, body, and revision_context.
    """
    result = revise_draft(
        original_body=original_body,
        original_subject=original_subject,
        feedback_categories=feedback_categories.split(",") if feedback_categories else [],
        comments=comments or None,
        guidance=guidance or None,
    )
    return json.dumps(result)
