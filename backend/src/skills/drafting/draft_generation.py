"""Draft generation skill — create outreach emails from templates."""
from src.models.email_draft import DraftGenerationInput


TEMPLATES = {
    "introduction": {
        "subject": "Exploring Gold Trade Opportunities in {country}",
        "body": """Dear {name},

I hope this message finds you well. I am reaching out on behalf of our organization, which is actively exploring gold trade partnerships in {country}.

We noticed {company_name} and your work in the gold sector, and we would be interested in exploring potential collaboration opportunities.

{personalization}

Would you be open to a brief conversation to discuss how we might work together?

Best regards""",
    },
    "partnership": {
        "subject": "Partnership Inquiry - {company_name}",
        "body": """Dear {name},

We are an international organization facilitating gold trade across Africa, and we are seeking strategic partners in {country}.

{company_name} has come to our attention as a significant player in the sector, and we believe there could be mutual benefit in exploring a partnership.

{personalization}

I would welcome the opportunity to discuss this further at your convenience.

Warm regards""",
    },
    "information_request": {
        "subject": "Information Request - Gold Operations in {country}",
        "body": """Dear {name},

I am writing to learn more about {company_name}'s gold operations in {country}.

Our organization is conducting research into the gold trade landscape and would appreciate any information you might be able to share about your operations, capacity, and areas of focus.

{personalization}

Thank you for your time.

Kind regards""",
    },
}

TONE_ADJUSTMENTS = {
    "formal": "",
    "conversational": "Please feel free to reach out informally — we value open communication.",
    "partnership": "We approach all relationships as true partnerships, with shared benefit as the goal.",
}


def generate_draft(input_data: DraftGenerationInput) -> dict:
    """Generate an outreach email draft from a template.

    Args:
        input_data: Draft generation parameters including lead name, company,
                    country, tone, and template family

    Returns:
        Dict with subject, body, template_used
    """
    template = TEMPLATES.get(input_data.template_family, TEMPLATES["introduction"])
    tone_note = TONE_ADJUSTMENTS.get(input_data.outreach_tone, "")

    personalization = ""
    if input_data.lead_details:
        personalization = f"We understand that {input_data.lead_details}"
    if tone_note:
        personalization = (
            f"{personalization}\n\n{tone_note}" if personalization else tone_note
        )

    subject = template["subject"].format(
        country=input_data.country,
        company_name=input_data.company_name or "your organization",
        name=input_data.lead_name,
    )
    body = template["body"].format(
        country=input_data.country,
        company_name=input_data.company_name or "your organization",
        name=input_data.lead_name,
        personalization=personalization or "We look forward to connecting.",
    )

    return {
        "subject": subject,
        "body": body,
        "template_used": input_data.template_family,
    }


def revise_draft(
    original_body: str,
    original_subject: str,
    feedback_categories: list[str],
    comments: str | None = None,
    guidance: str | None = None,
) -> dict:
    """Revise a draft based on structured feedback.

    This is a placeholder — real revision uses the LLM agent with feedback context.

    Args:
        original_body: Current draft body
        original_subject: Current draft subject
        feedback_categories: Structured feedback categories
        comments: Free-form reviewer comments
        guidance: Specific guidance for revision

    Returns:
        Dict with subject, body, and revision_context
    """
    return {
        "subject": original_subject,
        "body": original_body,
        "revision_context": {
            "categories": feedback_categories,
            "comments": comments,
            "guidance": guidance,
        },
    }


SKILL_METADATA = {
    "id": "draft-generation",
    "version": "1.0.0",
    "description": "Generate outreach email from template + lead data",
}
