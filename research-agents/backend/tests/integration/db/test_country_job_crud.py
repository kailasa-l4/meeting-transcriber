"""Integration tests for CountryJob database operations."""
import uuid

from src.db.models import CountryJob, CountryJobStatus, Lead, LeadVerificationStatus


class TestCountryJobCRUD:
    def test_create_country_job(self, db_session):
        job = CountryJob(
            id=uuid.uuid4(),
            country="Uganda",
            status=CountryJobStatus.queued,
            created_by="test-user",
            user_context={"target_types": ["exporters"]},
        )
        db_session.add(job)
        db_session.flush()

        fetched = db_session.get(CountryJob, job.id)
        assert fetched is not None
        assert fetched.country == "Uganda"
        assert fetched.status == CountryJobStatus.queued
        assert fetched.user_context["target_types"] == ["exporters"]

    def test_create_lead_linked_to_job(self, db_session, sample_country_job):
        lead = Lead(
            id=uuid.uuid4(),
            country_job_id=sample_country_job.id,
            name="Test Gold Exporter",
            email="test@gold.ug",
            verification_status=LeadVerificationStatus.discovered,
            confidence_score=0.7,
        )
        db_session.add(lead)
        db_session.flush()

        fetched = db_session.get(Lead, lead.id)
        assert fetched.country_job_id == sample_country_job.id
        assert fetched.confidence_score == 0.7

    def test_job_leads_relationship(self, db_session, sample_country_job):
        for i in range(3):
            db_session.add(Lead(
                id=uuid.uuid4(),
                country_job_id=sample_country_job.id,
                name=f"Lead {i}",
                verification_status=LeadVerificationStatus.discovered,
            ))
        db_session.flush()

        job = db_session.get(CountryJob, sample_country_job.id)
        assert len(job.leads) == 3

    def test_update_job_status(self, db_session, sample_country_job):
        sample_country_job.status = CountryJobStatus.running
        sample_country_job.current_stage = "discovery_fanout"
        db_session.flush()

        fetched = db_session.get(CountryJob, sample_country_job.id)
        assert fetched.status == CountryJobStatus.running
        assert fetched.current_stage == "discovery_fanout"
