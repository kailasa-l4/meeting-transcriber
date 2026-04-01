from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import CountryJobStatus


class CountrySubmissionInput(BaseModel):
    """Input for starting a new country research workflow."""
    country: str = Field(..., min_length=1, max_length=100)
    target_types: list[str] | None = None
    regions: list[str] | None = None
    language_preference: str | None = None
    known_entities: list[str] | None = None
    outreach_tone: str | None = Field(None, pattern="^(formal|conversational|partnership)$")
    template_family: str | None = None
    exclusions: list[str] | None = None
    notes: str | None = None
    force_fresh_run: bool = False


class CountryJobResponse(BaseModel):
    """Response for a country job."""
    id: UUID
    country: str
    status: CountryJobStatus
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    agno_session_id: str | None = None
    current_stage: str | None = None
    summary_counts: dict | None = None
    error_message: str | None = None
    user_context: dict | None = None
    prior_job_ids: list[UUID] | None = None
    total_token_count: int = 0
    estimated_cost: float = 0.0

    model_config = {"from_attributes": True}


class CountryJobSummary(BaseModel):
    """Summary for session list view."""
    id: UUID
    country: str
    status: CountryJobStatus
    created_at: datetime
    updated_at: datetime
    current_stage: str | None = None
    lead_count: int = 0
    verified_count: int = 0
    avg_confidence: float = 0.0
    pending_drafts: int = 0
    sent_emails: int = 0
    error_message: str | None = None
    total_token_count: int = 0
    estimated_cost: float = 0.0

    model_config = {"from_attributes": True}
