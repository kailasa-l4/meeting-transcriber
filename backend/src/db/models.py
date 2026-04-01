import enum
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as PgEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.base import Base


# --- PostgreSQL Enum Types ---


class CountryJobStatus(str, enum.Enum):
    queued = "queued"
    seeding_knowledge = "seeding_knowledge"
    running = "running"
    waiting_for_approval = "waiting_for_approval"
    partially_completed = "partially_completed"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class LeadVerificationStatus(str, enum.Enum):
    discovered = "discovered"
    normalized = "normalized"
    verified = "verified"
    needs_review = "needs_review"
    rejected = "rejected"


class OutreachStatus(str, enum.Enum):
    not_started = "not_started"
    draft_generated = "draft_generated"
    pending_review = "pending_review"
    changes_requested = "changes_requested"
    draft_regenerating = "draft_regenerating"
    draft_regenerated = "draft_regenerated"
    approved = "approved"
    sending = "sending"
    sent = "sent"
    rejected = "rejected"
    send_failed = "send_failed"


class VerificationDimension(str, enum.Enum):
    entity = "entity"
    contact = "contact"
    source_quality = "source_quality"
    dedup = "dedup"


class KnowledgeType(str, enum.Enum):
    directory = "directory"
    registry = "registry"
    search_strategy = "search_strategy"
    locale = "locale"
    learning = "learning"


class ReviewAction(str, enum.Enum):
    approve = "approve"
    request_changes = "request_changes"
    reject = "reject"


# --- Models ---


class CountryJob(Base):
    __tablename__ = "country_jobs"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country = mapped_column(String(100), nullable=False, index=True)
    created_by = mapped_column(String(200))
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    status = mapped_column(
        PgEnum(CountryJobStatus, name="country_job_status", create_type=True),
        nullable=False,
        default=CountryJobStatus.queued,
    )
    agno_session_id = mapped_column(String(200))
    agno_run_id = mapped_column(String(200))
    current_stage = mapped_column(String(100))
    summary_counts = mapped_column(JSONB, default={})
    error_message = mapped_column(Text)
    user_context = mapped_column(JSONB, default={})
    prior_job_ids = mapped_column(ARRAY(UUID(as_uuid=True)), default=[])
    total_token_count = mapped_column(Integer, default=0)
    estimated_cost = mapped_column(Float, default=0.0)

    # Relationships
    leads = relationship("Lead", back_populates="country_job", cascade="all, delete-orphan")
    workflow_events = relationship(
        "WorkflowEvent", back_populates="country_job", cascade="all, delete-orphan"
    )
    email_drafts = relationship(
        "EmailDraft", back_populates="country_job", cascade="all, delete-orphan"
    )
    skill_invocations = relationship(
        "SkillInvocationLog", back_populates="country_job", cascade="all, delete-orphan"
    )


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_job_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("country_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    event_type = mapped_column(String(100), nullable=False)
    stage = mapped_column(String(100))
    payload = mapped_column(JSONB, default={})
    skill_invoked = mapped_column(String(200))
    token_count = mapped_column(Integer, default=0)

    country_job = relationship("CountryJob", back_populates="workflow_events")


class Lead(Base):
    __tablename__ = "leads"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_job_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("country_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = mapped_column(String(300), nullable=False)
    role_title = mapped_column(String(300))
    whatsapp = mapped_column(String(50))
    phone = mapped_column(String(50))
    details = mapped_column(Text)
    email = mapped_column(String(300), index=True)
    company_name = mapped_column(String(300))
    website = mapped_column(String(500))
    source_text = mapped_column(Text)
    source_urls = mapped_column(ARRAY(Text), default=[])
    source_count = mapped_column(Integer, default=0)
    verification_status = mapped_column(
        PgEnum(LeadVerificationStatus, name="lead_verification_status", create_type=True),
        default=LeadVerificationStatus.discovered,
    )
    confidence_score = mapped_column(Float, default=0.0)
    confidence_breakdown = mapped_column(JSONB, default={})
    discovery_skill_used = mapped_column(String(200))
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_leads_job_confidence", "country_job_id", confidence_score.desc()),
    )

    country_job = relationship("CountryJob", back_populates="leads")
    sources = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    verification_records = relationship(
        "VerificationRecord",
        back_populates="lead",
        cascade="all, delete-orphan",
        foreign_keys="[VerificationRecord.lead_id]",
    )
    email_drafts = relationship("EmailDraft", back_populates="lead", cascade="all, delete-orphan")
    send_logs = relationship("EmailSendLog", back_populates="lead", cascade="all, delete-orphan")


class LeadSource(Base):
    __tablename__ = "lead_sources"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url = mapped_column(Text)
    source_title = mapped_column(String(500))
    source_type = mapped_column(String(100))
    excerpt = mapped_column(Text)
    collected_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="sources")


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = mapped_column(
        PgEnum(LeadVerificationStatus, name="lead_verification_status", create_type=False),
        nullable=False,
    )
    confidence_score = mapped_column(Float, default=0.0)
    dimension = mapped_column(
        PgEnum(VerificationDimension, name="verification_dimension", create_type=True),
        nullable=False,
    )
    verifier_notes = mapped_column(Text)
    contradictions_found = mapped_column(Text)
    duplicate_of_lead_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL")
    )
    skill_used = mapped_column(String(200))
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead = relationship("Lead", back_populates="verification_records", foreign_keys=[lead_id])


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    country_job_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("country_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = mapped_column(Integer, nullable=False, default=1)
    subject = mapped_column(String(500), nullable=False)
    body = mapped_column(Text, nullable=False)
    status = mapped_column(
        PgEnum(OutreachStatus, name="outreach_status", create_type=True),
        nullable=False,
        default=OutreachStatus.draft_generated,
    )
    model_name = mapped_column(String(200))
    template_used = mapped_column(String(200))
    skill_used = mapped_column(String(200))
    generated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by_system = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_drafts_lead_version", "lead_id", "version_number"),)

    lead = relationship("Lead", back_populates="email_drafts")
    country_job = relationship("CountryJob", back_populates="email_drafts")
    review_actions = relationship(
        "DraftReviewAction", back_populates="email_draft", cascade="all, delete-orphan"
    )
    send_logs = relationship(
        "EmailSendLog", back_populates="email_draft", cascade="all, delete-orphan"
    )


class DraftReviewAction(Base):
    __tablename__ = "draft_review_actions"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_draft_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id = mapped_column(String(200), nullable=False)
    action = mapped_column(
        PgEnum(ReviewAction, name="review_action", create_type=True), nullable=False
    )
    structured_feedback_categories = mapped_column(ARRAY(Text), default=[])
    comments = mapped_column(Text)
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    email_draft = relationship("EmailDraft", back_populates="review_actions")


class EmailSendLog(Base):
    __tablename__ = "email_send_logs"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_draft_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    send_method = mapped_column(String(50), default="gws_gmail")
    provider_message_id = mapped_column(String(500))
    sent_at = mapped_column(DateTime(timezone=True))
    send_status = mapped_column(String(50), nullable=False, default="pending")
    failure_reason = mapped_column(Text)

    email_draft = relationship("EmailDraft", back_populates="send_logs")
    lead = relationship("Lead", back_populates="send_logs")


class SkillInvocationLog(Base):
    __tablename__ = "skill_invocation_logs"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_job_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("country_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name = mapped_column(String(200), nullable=False)
    skill_version = mapped_column(String(50))
    agent_name = mapped_column(String(200))
    input_summary = mapped_column(Text)
    output_summary = mapped_column(Text)
    token_count = mapped_column(Integer, default=0)
    duration_ms = mapped_column(Integer, default=0)
    status = mapped_column(String(50), nullable=False, default="running")
    error_message = mapped_column(Text)
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    country_job = relationship("CountryJob", back_populates="skill_invocations")


class CountryKnowledge(Base):
    __tablename__ = "country_knowledge"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country = mapped_column(String(100), nullable=False, index=True)
    knowledge_type = mapped_column(
        PgEnum(KnowledgeType, name="knowledge_type", create_type=True), nullable=False
    )
    content = mapped_column(JSONB, nullable=False)
    source = mapped_column(String(500))
    created_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_knowledge_country_type", "country", "knowledge_type"),)
