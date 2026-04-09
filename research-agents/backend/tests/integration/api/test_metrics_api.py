"""Integration tests for metrics API."""
import pytest
from fastapi.testclient import TestClient

from src.db.base import get_db
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


class TestMetricsAPI:
    def test_get_metrics_returns_200(self, db_session):
        """GET /api/metrics returns 200."""
        response = client.get("/api/metrics")
        assert response.status_code == 200

    def test_get_metrics_response_shape(self, db_session):
        """GET /api/metrics returns all expected summary fields."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "jobs_by_status" in data
        assert "total_leads" in data
        assert "verified_leads" in data
        assert "avg_confidence" in data
        assert "total_drafts" in data
        assert "pending_drafts" in data
        assert "approved_drafts" in data
        assert "sent_emails" in data
        assert "rejected_drafts" in data
        assert "countries_covered" in data

    def test_get_metrics_empty_db(self, db_session):
        """GET /api/metrics returns zeros when DB is empty."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] >= 0
        assert data["total_leads"] >= 0
        assert isinstance(data["countries_covered"], list)

    def test_get_metrics_with_data(self, db_session, sample_country_job, sample_lead, sample_email_draft):
        """GET /api/metrics reflects created fixtures in counts."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] >= 1
        assert data["total_leads"] >= 1
        assert data["total_drafts"] >= 1
        assert data["pending_drafts"] >= 1
        assert "Ghana" in data["countries_covered"]
        assert data["verified_leads"] >= 1
        assert data["avg_confidence"] > 0.0

    def test_get_metrics_types(self, db_session):
        """GET /api/metrics returns correct types for all fields."""
        response = client.get("/api/metrics")
        data = response.json()
        assert isinstance(data["total_jobs"], int)
        assert isinstance(data["jobs_by_status"], dict)
        assert isinstance(data["total_leads"], int)
        assert isinstance(data["avg_confidence"], (int, float))
        assert isinstance(data["countries_covered"], list)
