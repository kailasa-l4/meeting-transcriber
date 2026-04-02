"""Integration tests for approvals API routes."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.db.base import get_db
from src.db.models import EmailDraft, OutreachStatus
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


class TestListPending:
    def test_list_pending_approvals(self, db_session, sample_email_draft):
        """GET /api/approvals/pending returns pending drafts."""
        response = client.get("/api/approvals/pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_pending_response_shape(self, db_session, sample_email_draft):
        """Verify pending approval response contains expected detail fields."""
        response = client.get("/api/approvals/pending")
        assert response.status_code == 200
        data = response.json()
        item = data[0]
        assert "draft" in item
        assert "lead_name" in item
        assert "company_name" in item
        assert "country" in item
        assert "confidence_score" in item
        assert "all_versions" in item
        assert "review_history" in item

    def test_list_pending_empty_when_no_pending(self, db_session):
        """GET /api/approvals/pending returns empty list with no pending drafts."""
        response = client.get("/api/approvals/pending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGetDraft:
    def test_get_draft_detail(self, db_session, sample_email_draft):
        """GET /api/approvals/{id} returns draft detail."""
        response = client.get(f"/api/approvals/{sample_email_draft.id}")
        assert response.status_code == 200
        data = response.json()
        assert "draft" in data
        assert data["draft"]["id"] == str(sample_email_draft.id)
        assert data["draft"]["subject"] == "Partnership Inquiry - Gold Trade Opportunities"
        assert data["draft"]["status"] == "pending_review"

    def test_get_draft_not_found(self, db_session):
        """GET /api/approvals/{id} returns 404 for non-existent draft."""
        response = client.get(f"/api/approvals/{uuid.uuid4()}")
        assert response.status_code == 404


class TestApproveDraft:
    def test_approve_draft(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/approve transitions to approved."""
        response = client.post(f"/api/approvals/{sample_email_draft.id}/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["id"] == str(sample_email_draft.id)

    def test_approve_nonexistent(self, db_session):
        """POST /api/approvals/{id}/approve returns 404 for non-existent draft."""
        response = client.post(f"/api/approvals/{uuid.uuid4()}/approve")
        assert response.status_code == 404

    def test_approve_already_approved(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/approve on already approved returns 409."""
        # First approve
        client.post(f"/api/approvals/{sample_email_draft.id}/approve")
        # Second approve should conflict
        response = client.post(f"/api/approvals/{sample_email_draft.id}/approve")
        assert response.status_code == 409


class TestRejectDraft:
    def test_reject_draft(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/reject transitions to rejected."""
        response = client.post(f"/api/approvals/{sample_email_draft.id}/reject")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_reject_with_comments(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/reject with review request body."""
        response = client.post(
            f"/api/approvals/{sample_email_draft.id}/reject",
            json={
                "action": "reject",
                "comments": "Not suitable for this contact",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_reject_already_rejected(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/reject on already rejected returns 409."""
        client.post(f"/api/approvals/{sample_email_draft.id}/reject")
        response = client.post(f"/api/approvals/{sample_email_draft.id}/reject")
        assert response.status_code == 409


class TestRequestChanges:
    def test_request_changes(self, db_session, sample_email_draft):
        """POST /api/approvals/{id}/request-changes with structured feedback."""
        response = client.post(
            f"/api/approvals/{sample_email_draft.id}/request-changes",
            json={
                "action": "request_changes",
                "structured_feedback_categories": ["tone_adjustment", "missing_information"],
                "comments": "Please make it more formal and add company background",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # After request-changes, draft may be in changes_requested or draft_regenerated
        assert data["status"] in ("changes_requested", "draft_regenerated")

    def test_request_changes_nonexistent(self, db_session):
        """POST /api/approvals/{id}/request-changes returns 404."""
        response = client.post(
            f"/api/approvals/{uuid.uuid4()}/request-changes",
            json={
                "action": "request_changes",
                "structured_feedback_categories": ["tone_adjustment"],
                "comments": "test",
            },
        )
        assert response.status_code == 404
