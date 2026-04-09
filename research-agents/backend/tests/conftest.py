"""Shared test fixtures for the Gold Lead Research System."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import Settings
from src.db.base import Base
from src.db.models import (
    CountryJob, Lead, LeadSource, VerificationRecord,
    EmailDraft, DraftReviewAction, EmailSendLog,
    WorkflowEvent, SkillInvocationLog, CountryKnowledge,
    CountryJobStatus, LeadVerificationStatus, OutreachStatus,
    VerificationDimension, KnowledgeType, ReviewAction,
)


@pytest.fixture(scope="session")
def test_settings():
    """Test settings using the test database."""
    return Settings(
        database_url="postgresql+psycopg://goldleads:goldleads_dev@localhost:5433/goldleads_test"
    )


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """SQLAlchemy engine for the test database."""
    engine = create_engine(test_settings.database_url, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Database session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_country_job(db_session):
    """A sample CountryJob for testing."""
    job = CountryJob(
        id=uuid.uuid4(),
        country="Ghana",
        status=CountryJobStatus.queued,
        created_by="test-user",
        user_context={"target_types": ["miners", "brokers"]},
    )
    db_session.add(job)
    db_session.flush()
    return job


@pytest.fixture
def sample_lead(db_session, sample_country_job):
    """A sample Lead for testing."""
    lead = Lead(
        id=uuid.uuid4(),
        country_job_id=sample_country_job.id,
        name="Acme Gold Mining Ltd",
        role_title="Managing Director",
        email="info@acmegold.com.gh",
        company_name="Acme Gold Mining",
        website="https://acmegold.com.gh",
        phone="+233241234567",
        verification_status=LeadVerificationStatus.verified,
        confidence_score=0.85,
        confidence_breakdown={
            "entity": 0.9,
            "contact": 0.8,
            "source_quality": 0.85,
            "dedup": 1.0,
        },
        source_count=3,
    )
    db_session.add(lead)
    db_session.flush()
    return lead


@pytest.fixture
def sample_email_draft(db_session, sample_lead, sample_country_job):
    """A sample EmailDraft for testing."""
    draft = EmailDraft(
        id=uuid.uuid4(),
        lead_id=sample_lead.id,
        country_job_id=sample_country_job.id,
        version_number=1,
        subject="Partnership Inquiry - Gold Trade Opportunities",
        body="Dear Managing Director,\n\nWe are writing to explore...",
        status=OutreachStatus.pending_review,
        template_used="introduction",
    )
    db_session.add(draft)
    db_session.flush()
    return draft
