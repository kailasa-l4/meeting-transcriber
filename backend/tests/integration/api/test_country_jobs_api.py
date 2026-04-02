"""Integration tests for country jobs API routes."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.db.base import get_db
from src.db.models import CountryJob, CountryJobStatus
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


class TestListJobs:
    def test_list_jobs_empty(self, db_session):
        """GET /api/jobs returns empty list when no jobs exist in fresh session."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_jobs_contains_created_job(self, db_session, sample_country_job):
        """GET /api/jobs includes a job we just created via fixture."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        ids = [item["id"] for item in data]
        assert str(sample_country_job.id) in ids

    def test_list_jobs_filter_by_country(self, db_session, sample_country_job):
        """GET /api/jobs?country=Ghana filters results by country."""
        response = client.get("/api/jobs?country=Ghana")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for item in data:
            assert "ghana" in item["country"].lower()

    def test_list_jobs_filter_by_status(self, db_session, sample_country_job):
        """GET /api/jobs?status=queued filters by status."""
        response = client.get("/api/jobs?status=queued")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["status"] == "queued"

    def test_list_jobs_summary_fields(self, db_session, sample_country_job):
        """GET /api/jobs returns summary fields including computed counts."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        job_data = next(j for j in data if j["id"] == str(sample_country_job.id))
        assert "lead_count" in job_data
        assert "verified_count" in job_data
        assert "avg_confidence" in job_data
        assert "pending_drafts" in job_data
        assert "sent_emails" in job_data


class TestCreateJob:
    def test_create_job(self, db_session):
        """POST /api/jobs creates a new country job."""
        response = client.post("/api/jobs", json={
            "country": "Ghana",
            "target_types": ["miners", "brokers"],
            "outreach_tone": "formal",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["country"] == "Ghana"
        assert data["status"] == "queued"
        assert data["id"] is not None

    def test_create_job_minimal(self, db_session):
        """POST /api/jobs with only required field (country)."""
        response = client.post("/api/jobs", json={"country": "Kenya"})
        assert response.status_code == 201
        data = response.json()
        assert data["country"] == "Kenya"
        assert data["status"] == "queued"

    def test_create_job_missing_country(self, db_session):
        """POST /api/jobs without country returns 422."""
        response = client.post("/api/jobs", json={})
        assert response.status_code == 422

    def test_create_job_all_options(self, db_session):
        """POST /api/jobs with all optional fields."""
        response = client.post("/api/jobs", json={
            "country": "Uganda",
            "target_types": ["miners", "brokers", "exporters"],
            "regions": ["Kampala", "Entebbe"],
            "language_preference": "en",
            "known_entities": ["Uganda Gold Corp"],
            "outreach_tone": "partnership",
            "template_family": "partnership",
            "exclusions": ["competitor_co"],
            "notes": "Focus on artisanal miners",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["country"] == "Uganda"
        assert data["user_context"]["target_types"] == ["miners", "brokers", "exporters"]


class TestGetJob:
    def test_get_job_by_id(self, db_session, sample_country_job):
        """GET /api/jobs/{id} returns the job."""
        response = client.get(f"/api/jobs/{sample_country_job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "Ghana"
        assert data["id"] == str(sample_country_job.id)
        assert data["status"] == "queued"

    def test_get_job_not_found(self, db_session):
        """GET /api/jobs/{id} returns 404 for non-existent job."""
        response = client.get(f"/api/jobs/{uuid.uuid4()}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_invalid_uuid(self, db_session):
        """GET /api/jobs/invalid returns 422."""
        response = client.get("/api/jobs/not-a-uuid")
        assert response.status_code == 422


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        """GET /health returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
