"""Unit tests for the dedup resolver skill."""
import uuid

from src.models.lead import NormalizedLead
from src.skills.verification.dedup_resolver import (
    _extract_domain,
    _normalize_company,
    _normalize_phone,
    check_duplicate,
)

# Fixed UUIDs for test existing leads
EXISTING_UUID_1 = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
EXISTING_UUID_2 = str(uuid.UUID("22222222-2222-2222-2222-222222222222"))


class TestCheckDuplicate:
    def test_exact_email_match(self):
        """Exact email match flags duplicate with score 1.0."""
        candidate = NormalizedLead(name="John", email="john@acme.com")
        existing = [{"id": EXISTING_UUID_1, "email": "john@acme.com", "company_name": "Acme"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True
        assert result.score == 1.0
        assert result.dimension.value == "dedup"

    def test_email_match_case_insensitive(self):
        """Email matching is case-insensitive."""
        candidate = NormalizedLead(name="John", email="JOHN@Acme.COM")
        existing = [{"id": EXISTING_UUID_1, "email": "john@acme.com"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True

    def test_company_name_match(self):
        """Normalized company name match flags duplicate."""
        candidate = NormalizedLead(name="John", company_name="Acme Gold Ltd")
        existing = [{"id": EXISTING_UUID_1, "email": "x@y.com", "company_name": "Acme Gold"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True
        assert result.score == 0.9

    def test_phone_match(self):
        """Phone number match after normalization flags duplicate."""
        candidate = NormalizedLead(name="John", phone="+233241234567")
        existing = [{"id": EXISTING_UUID_1, "phone": "+233-24-123-4567"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True
        assert result.score == 0.85

    def test_website_domain_match(self):
        """Website domain match flags duplicate."""
        candidate = NormalizedLead(name="John", website="https://acmegold.com")
        existing = [{"id": EXISTING_UUID_1, "website": "https://www.acmegold.com"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True
        assert result.score == 0.8

    def test_no_duplicate(self):
        """No matching fields means no duplicate."""
        candidate = NormalizedLead(name="John", email="john@newco.com", company_name="New Co")
        existing = [{"id": EXISTING_UUID_1, "email": "jane@acme.com", "company_name": "Acme"}]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is False
        assert result.score == 1.0  # confidence the lead is unique

    def test_empty_existing(self):
        """Empty existing list means no duplicate."""
        candidate = NormalizedLead(name="John")
        result = check_duplicate(candidate, [])
        assert result.is_duplicate is False

    def test_multiple_existing_first_match_wins(self):
        """First matching lead is returned as duplicate."""
        candidate = NormalizedLead(name="John", email="john@acme.com")
        existing = [
            {"id": EXISTING_UUID_1, "email": "john@acme.com"},
            {"id": EXISTING_UUID_2, "email": "john@acme.com"},
        ]
        result = check_duplicate(candidate, existing)
        assert result.is_duplicate is True
        assert str(result.duplicate_of_lead_id) == EXISTING_UUID_1

    def test_skill_used_field(self):
        """Result always includes the skill_used field."""
        candidate = NormalizedLead(name="John")
        result = check_duplicate(candidate, [])
        assert result.skill_used == "dedup-resolver"


class TestNormalizeCompany:
    def test_strips_ltd(self):
        assert _normalize_company("Acme Gold Ltd") == "acme gold"

    def test_strips_limited(self):
        # "Mining Corp Limited" -> strips " limited" -> "mining corp" -> strips " corp" -> "mining"
        # The function strips ALL matching suffixes in sequence
        assert _normalize_company("Mining Corp Limited") == "mining"

    def test_strips_inc(self):
        assert _normalize_company("GoldCo Inc") == "goldco"

    def test_strips_plc(self):
        assert _normalize_company("Royal Gold Plc") == "royal gold"

    def test_strips_whitespace(self):
        # "Test Company Limited" -> strips " limited" -> "test company"
        # No further suffix matches, so final result is "test company"
        assert _normalize_company("  Test Company Limited  ") == "test company"

    def test_preserves_core_name(self):
        # "Mining Corp" -> strips " corp" -> "mining"
        assert _normalize_company("Mining Corp") == "mining"

    def test_no_suffix_to_strip(self):
        assert _normalize_company("Golden Star Miners") == "golden star miners"

    def test_strips_llc(self):
        assert _normalize_company("Gold Trade LLC") == "gold trade"

    def test_strips_gmbh(self):
        assert _normalize_company("Gold Handel GmbH") == "gold handel"


class TestNormalizePhone:
    def test_strips_formatting(self):
        assert _normalize_phone("+233-24-123-4567") == "+233241234567"

    def test_keeps_plus_and_digits(self):
        assert _normalize_phone("+1 (555) 123-4567") == "+15551234567"


class TestExtractDomain:
    def test_strips_https(self):
        assert _extract_domain("https://acmegold.com") == "acmegold.com"

    def test_strips_http(self):
        assert _extract_domain("http://acmegold.com") == "acmegold.com"

    def test_strips_www(self):
        assert _extract_domain("https://www.acmegold.com") == "acmegold.com"

    def test_strips_path(self):
        assert _extract_domain("https://acmegold.com/about") == "acmegold.com"

    def test_bare_domain(self):
        assert _extract_domain("acmegold.com") == "acmegold.com"
