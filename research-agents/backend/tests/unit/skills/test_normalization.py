"""Unit tests for the normalization skill."""
from src.models.lead import RawCandidate
from src.skills.normalization.normalize import (
    _clean_name,
    _normalize_email,
    _normalize_phone,
    _normalize_url,
    normalize_lead,
)


class TestNormalizeLead:
    def test_normalize_basic_lead(self):
        """Normalizes name, email, and preserves company."""
        raw = RawCandidate(name="John Doe", email="JOHN@MINING.CO", company_name="Acme Gold")
        result = normalize_lead(raw)
        assert result.name == "John Doe"
        assert result.email == "john@mining.co"
        assert result.company_name == "Acme Gold"

    def test_normalize_lead_with_source(self):
        """Tracks source URL and source count."""
        raw = RawCandidate(
            name="Test Lead",
            source_url="https://example.com",
            source_excerpt="Gold mining company",
            discovery_skill="discovery-miners",
        )
        result = normalize_lead(raw)
        assert result.source_urls == ["https://example.com"]
        assert result.source_count == 1
        assert result.discovery_skill_used == "discovery-miners"
        assert result.source_text == "Gold mining company"

    def test_normalize_lead_without_source(self):
        """No source URL produces empty source list and zero count."""
        raw = RawCandidate(name="Bare Lead")
        result = normalize_lead(raw)
        assert result.source_urls == []
        assert result.source_count == 0
        assert result.discovery_skill_used is None

    def test_normalize_lead_with_all_fields(self):
        """All fields are mapped correctly."""
        raw = RawCandidate(
            name="Jane Smith",
            role_title="CEO",
            whatsapp="+233 24 123 4567",
            phone="+233-24-123-4567",
            details="Major gold operation",
            email="  JANE@Mining.GH  ",
            company_name="GoldCo Ltd",
            website="mining.gh",
            source_url="https://directory.com/goldco",
            source_excerpt="Listed in directory",
            discovery_skill="directory-scanner",
        )
        result = normalize_lead(raw)
        assert result.name == "Jane Smith"
        assert result.role_title == "CEO"
        assert result.whatsapp == "+233241234567"
        assert result.phone == "+233241234567"
        assert result.email == "jane@mining.gh"
        assert result.website == "https://mining.gh"
        assert result.source_urls == ["https://directory.com/goldco"]
        assert result.source_count == 1

    def test_normalize_lead_empty_name_whitespace(self):
        """Extra whitespace in name is cleaned."""
        raw = RawCandidate(name="  John    Doe  ")
        result = normalize_lead(raw)
        assert result.name == "John Doe"


class TestNormalizePhone:
    def test_strips_dashes(self):
        assert _normalize_phone("+233-24-123-4567") == "+233241234567"

    def test_strips_spaces_and_parens(self):
        assert _normalize_phone("+233 (24) 123 4567") == "+233241234567"

    def test_strips_dots(self):
        assert _normalize_phone("+1.555.123.4567") == "+15551234567"

    def test_none_returns_none(self):
        assert _normalize_phone(None) is None

    def test_empty_string_returns_none(self):
        assert _normalize_phone("") is None


class TestNormalizeEmail:
    def test_lowercases_and_strips(self):
        assert _normalize_email("  JOHN@Mining.CO  ") == "john@mining.co"

    def test_already_lowercase(self):
        assert _normalize_email("john@mining.co") == "john@mining.co"

    def test_none_returns_none(self):
        assert _normalize_email(None) is None

    def test_empty_string(self):
        assert _normalize_email("") is None


class TestNormalizeUrl:
    def test_adds_https_scheme(self):
        assert _normalize_url("mining.com") == "https://mining.com"

    def test_preserves_existing_https(self):
        assert _normalize_url("https://mining.com") == "https://mining.com"

    def test_preserves_existing_http(self):
        assert _normalize_url("http://mining.com") == "http://mining.com"

    def test_none_returns_none(self):
        assert _normalize_url(None) is None

    def test_empty_string_returns_none(self):
        assert _normalize_url("") is None

    def test_strips_whitespace(self):
        assert _normalize_url("  mining.com  ") == "https://mining.com"


class TestCleanName:
    def test_collapses_whitespace(self):
        assert _clean_name("  John    Doe  ") == "John Doe"

    def test_empty_string(self):
        assert _clean_name("") == ""

    def test_single_name(self):
        assert _clean_name("John") == "John"
