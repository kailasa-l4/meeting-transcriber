from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import OutreachStatus, ReviewAction, StructuredFeedbackCategory


class DraftGenerationInput(BaseModel):
    """Input for draft generation skill."""
    lead_name: str
    company_name: str | None = None
    country: str
    lead_details: str | None = None
    outreach_tone: str = "formal"
    template_family: str = "introduction"
    language: str = "en"


class EmailDraftResponse(BaseModel):
    """Email draft for API response."""
    id: UUID
    lead_id: UUID
    country_job_id: UUID
    version_number: int
    subject: str
    body: str
    status: OutreachStatus
    model_name: str | None = None
    template_used: str | None = None
    skill_used: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class DraftReviewRequest(BaseModel):
    """Request to review a draft (approve, request changes, or reject)."""
    action: ReviewAction
    structured_feedback_categories: list[StructuredFeedbackCategory] = Field(default_factory=list)
    comments: str | None = None
    guidance: str | None = None


class DraftReviewActionResponse(BaseModel):
    """Review action record for API response."""
    id: UUID
    email_draft_id: UUID
    reviewer_id: str
    action: ReviewAction
    structured_feedback_categories: list[str] = []
    comments: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailSendLogResponse(BaseModel):
    """Send log for API response."""
    id: UUID
    email_draft_id: UUID
    lead_id: UUID
    send_method: str
    provider_message_id: str | None = None
    sent_at: datetime | None = None
    send_status: str
    failure_reason: str | None = None

    model_config = {"from_attributes": True}


class DraftDetailResponse(BaseModel):
    """Full draft detail with version history and reviews."""
    draft: EmailDraftResponse
    lead_name: str
    company_name: str | None = None
    country: str
    confidence_score: float = 0.0
    template_used: str | None = None
    all_versions: list[EmailDraftResponse] = []
    review_history: list[DraftReviewActionResponse] = []
