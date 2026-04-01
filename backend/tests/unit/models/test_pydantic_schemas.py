"""Unit tests for Pydantic schema validation."""
import uuid

import pytest
from pydantic import ValidationError

from src.models.lead import NormalizedLead, RawCandidate, LeadResponse
from src.models.country_job import CountrySubmissionInput, CountryJobResponse
from src.models.email_draft import DraftReviewRequest
from src.models.verification import VerificationResult
from src.models.enums import (
    CountryJobStatus, ReviewAction, StructuredFeedbackCategory,
    VerificationDimension,
)


class TestNormalizedLead:
    def test_valid_lead(self):
        lead = NormalizedLead(name="Test Mining Co", email="test@mining.co", confidence_score=0.85)
        assert lead.name == "Test Mining Co"
        assert lead.confidence_score == 0.85
        assert lead.is_duplicate is False

    def test_name_required(self):
        with pytest.raises(ValidationError):
            NormalizedLead(name="", confidence_score=0.5)

    def test_confidence_score_range(self):
        with pytest.raises(ValidationError):
            NormalizedLead(name="Test", confidence_score=1.5)
        with pytest.raises(ValidationError):
            NormalizedLead(name="Test", confidence_score=-0.1)

    def test_phone_strip_formatting(self):
        lead = NormalizedLead(name="Test", phone="+233-24-123-4567")
        assert lead.phone == "+233241234567"

    def test_whatsapp_strip_formatting(self):
        lead = NormalizedLead(name="Test", whatsapp="+233 (24) 123 4567")
        assert lead.whatsapp == "+233241234567"

    def test_defaults(self):
        lead = NormalizedLead(name="Test")
        assert lead.source_urls == []
        assert lead.confidence_score == 0.0
        assert lead.confidence_breakdown == {}


class TestCountrySubmissionInput:
    def test_valid_submission(self):
        inp = CountrySubmissionInput(country="Ghana")
        assert inp.country == "Ghana"
        assert inp.force_fresh_run is False

    def test_country_required(self):
        with pytest.raises(ValidationError):
            CountrySubmissionInput(country="")

    def test_optional_fields(self):
        inp = CountrySubmissionInput(
            country="Kenya",
            target_types=["miners", "brokers"],
            regions=["Nairobi"],
            outreach_tone="formal",
        )
        assert inp.target_types == ["miners", "brokers"]

    def test_invalid_outreach_tone(self):
        with pytest.raises(ValidationError):
            CountrySubmissionInput(country="Ghana", outreach_tone="aggressive")


class TestDraftReviewRequest:
    def test_approve(self):
        req = DraftReviewRequest(action=ReviewAction.approve)
        assert req.action == ReviewAction.approve

    def test_request_changes_with_feedback(self):
        req = DraftReviewRequest(
            action=ReviewAction.request_changes,
            structured_feedback_categories=[
                StructuredFeedbackCategory.tone_adjustment,
                StructuredFeedbackCategory.missing_information,
            ],
            comments="Please make it more formal",
        )
        assert len(req.structured_feedback_categories) == 2


class TestVerificationResult:
    def test_valid_result(self):
        result = VerificationResult(
            dimension=VerificationDimension.entity,
            score=0.9,
            rationale="Company appears in Ghana mining registry",
        )
        assert result.score == 0.9

    def test_score_range(self):
        with pytest.raises(ValidationError):
            VerificationResult(
                dimension=VerificationDimension.entity,
                score=1.5,
                rationale="test",
            )
