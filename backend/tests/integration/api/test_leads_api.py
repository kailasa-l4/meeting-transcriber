"""Integration tests for leads API routes."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.db.base import get_db
from src.db.models import Lead, LeadVerificationStatus
from src.main import app


@pytest.fixture(autouse=True)
def _override_db(db_session):
    """Override the FastAPI get_db dependency with the test session."""

    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


class TestListLeads:
    def test_list_leads_returns_list(self, db_session, sample_lead):
        """GET /api/leads returns a list of leads."""
        response = client.get("/api/leads")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_leads_filter_by_job(self, db_session, sample_lead, sample_country_job):
        """GET /api/leads?job_id=X filters by country job."""
        response = client.get(f"/api/leads?job_id={sample_country_job.id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for lead in data:
            assert lead["country_job_id"] == str(sample_country_job.id)

    def test_list_leads_filter_by_min_confidence(self, db_session, sample_lead):
        """GET /api/leads?min_confidence=0.8 filters by score."""
        response = client.get("/api/leads?min_confidence=0.8")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for lead in data:
            assert lead["confidence_score"] >= 0.8

    def test_list_leads_filter_by_high_confidence_excludes_low(self, db_session, sample_lead):
        """GET /api/leads?min_confidence=0.99 excludes leads below threshold."""
        response = client.get("/api/leads?min_confidence=0.99")
        assert response.status_code == 200
        data = response.json()
        # sample_lead has confidence 0.85, should be excluded
        ids = [l["id"] for l in data]
        assert str(sample_lead.id) not in ids

    def test_list_leads_filter_by_status(self, db_session, sample_lead):
        """GET /api/leads?status=verified filters by verification status."""
        response = client.get("/api/leads?status=verified")
        assert response.status_code == 200
        data = response.json()
        for lead in data:
            assert lead["verification_status"] == "verified"

    def test_list_leads_pagination(self, db_session, sample_lead):
        """GET /api/leads?limit=1&offset=0 respects pagination params."""
        response = client.get("/api/leads?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1

    def test_list_leads_response_shape(self, db_session, sample_lead):
        """Verify lead list response has the expected fields."""
        response = client.get("/api/leads")
        assert response.status_code == 200
        data = response.json()
        lead_data = data[0]
        assert "id" in lead_data
        assert "country_job_id" in lead_data
        assert "name" in lead_data
        assert "email" in lead_data
        assert "company_name" in lead_data
        assert "verification_status" in lead_data
        assert "confidence_score" in lead_data


class TestGetLead:
    def test_get_lead_detail(self, db_session, sample_lead):
        """GET /api/leads/{id} returns full lead detail."""
        response = client.get(f"/api/leads/{sample_lead.id}")
        assert response.status_code == 200
        data = response.json()
        assert "lead" in data
        assert "sources" in data
        assert "verification_records" in data
        assert "draft_status" in data
        assert data["lead"]["name"] == "Acme Gold Mining Ltd"
        assert data["lead"]["email"] == "info@acmegold.com.gh"

    def test_get_lead_not_found(self, db_session):
        """GET /api/leads/{id} returns 404 for non-existent lead."""
        response = client.get(f"/api/leads/{uuid.uuid4()}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_lead_invalid_uuid(self, db_session):
        """GET /api/leads/invalid returns 422."""
        response = client.get("/api/leads/not-a-uuid")
        assert response.status_code == 422

    def test_get_lead_with_draft(self, db_session, sample_lead, sample_email_draft):
        """GET /api/leads/{id} includes draft_status when a draft exists."""
        response = client.get(f"/api/leads/{sample_lead.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["draft_status"] is not None
        assert data["draft_status"] == "pending_review"
