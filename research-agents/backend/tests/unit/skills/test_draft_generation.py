"""Unit tests for the draft generation skill."""
from src.models.email_draft import DraftGenerationInput
from src.skills.drafting.draft_generation import (
    TEMPLATES,
    TONE_ADJUSTMENTS,
    generate_draft,
    revise_draft,
)


class TestGenerateDraft:
    def test_generate_introduction_draft(self):
        """Default template generates an introduction email."""
        input_data = DraftGenerationInput(
            lead_name="John Doe",
            company_name="Acme Gold Mining",
            country="Ghana",
        )
        result = generate_draft(input_data)
        assert "subject" in result
        assert "body" in result
        assert "template_used" in result
        assert "Ghana" in result["subject"]
        assert "John Doe" in result["body"]
        assert "Acme Gold Mining" in result["body"]
        assert result["template_used"] == "introduction"

    def test_generate_partnership_draft(self):
        """Partnership template generates a partnership email."""
        input_data = DraftGenerationInput(
            lead_name="Jane Smith",
            company_name="Kenya Gold Exports",
            country="Kenya",
            template_family="partnership",
            outreach_tone="partnership",
        )
        result = generate_draft(input_data)
        assert "Kenya Gold Exports" in result["body"]
        assert "Kenya" in result["subject"]
        assert result["template_used"] == "partnership"

    def test_generate_information_request_draft(self):
        """Information request template generates an inquiry email."""
        input_data = DraftGenerationInput(
            lead_name="Test User",
            company_name="Mining Corp",
            country="Uganda",
            template_family="information_request",
        )
        result = generate_draft(input_data)
        assert "Information Request" in result["subject"]
        assert "Mining Corp" in result["body"]
        assert result["template_used"] == "information_request"

    def test_generate_draft_with_details(self):
        """Lead details are included as personalization."""
        input_data = DraftGenerationInput(
            lead_name="John Doe",
            company_name="Acme",
            country="Ghana",
            lead_details="you process 500kg of gold monthly",
        )
        result = generate_draft(input_data)
        assert "you process 500kg of gold monthly" in result["body"]

    def test_generate_draft_with_tone(self):
        """Tone adjustments are included in the body."""
        input_data = DraftGenerationInput(
            lead_name="John Doe",
            company_name="Acme",
            country="Ghana",
            outreach_tone="conversational",
        )
        result = generate_draft(input_data)
        assert "open communication" in result["body"].lower() or "informally" in result["body"].lower()

    def test_generate_draft_no_company(self):
        """Missing company name uses fallback text."""
        input_data = DraftGenerationInput(
            lead_name="John Doe",
            country="Ghana",
        )
        result = generate_draft(input_data)
        assert "your organization" in result["body"]

    def test_fallback_to_introduction_for_unknown_template(self):
        """Unknown template_family falls back to introduction."""
        input_data = DraftGenerationInput(
            lead_name="John Doe",
            company_name="Acme",
            country="Ghana",
            template_family="nonexistent",
        )
        result = generate_draft(input_data)
        # Falls back to introduction template content
        assert "subject" in result
        assert "body" in result


class TestTemplates:
    def test_all_expected_templates_exist(self):
        """All three expected templates are registered."""
        assert "introduction" in TEMPLATES
        assert "partnership" in TEMPLATES
        assert "information_request" in TEMPLATES

    def test_templates_have_required_fields(self):
        """Each template must have subject and body keys."""
        for name, template in TEMPLATES.items():
            assert "subject" in template, f"Template '{name}' missing subject"
            assert "body" in template, f"Template '{name}' missing body"

    def test_templates_have_placeholders(self):
        """Templates contain the required format placeholders."""
        for name, template in TEMPLATES.items():
            assert "{country}" in template["subject"] or "{company_name}" in template["subject"], \
                f"Template '{name}' subject has no dynamic placeholder"
            assert "{name}" in template["body"], f"Template '{name}' body missing {{name}}"
            assert "{country}" in template["body"], f"Template '{name}' body missing {{country}}"

    def test_tone_adjustments_exist(self):
        """Tone adjustment strings are defined."""
        assert "formal" in TONE_ADJUSTMENTS
        assert "conversational" in TONE_ADJUSTMENTS
        assert "partnership" in TONE_ADJUSTMENTS


class TestReviseDraft:
    def test_revise_returns_structure(self):
        """Revise draft returns subject, body, and revision context."""
        result = revise_draft(
            original_body="Dear John...",
            original_subject="Partnership Inquiry",
            feedback_categories=["tone_adjustment"],
            comments="Make it more formal",
            guidance="Use professional tone",
        )
        assert "subject" in result
        assert "body" in result
        assert "revision_context" in result
        assert result["revision_context"]["categories"] == ["tone_adjustment"]
        assert result["revision_context"]["comments"] == "Make it more formal"
        assert result["revision_context"]["guidance"] == "Use professional tone"
