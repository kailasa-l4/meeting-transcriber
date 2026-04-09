from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import LeadVerificationStatus, VerificationDimension


class VerificationResult(BaseModel):
    """Output from a verification skill."""
    dimension: VerificationDimension
    score: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    contradictions: str | None = None
    is_duplicate: bool = False
    duplicate_of_lead_id: UUID | None = None
    skill_used: str | None = None


class VerificationRecordResponse(BaseModel):
    """Verification record for API response."""
    id: UUID
    lead_id: UUID
    status: LeadVerificationStatus
    confidence_score: float
    dimension: VerificationDimension
    verifier_notes: str | None = None
    contradictions_found: str | None = None
    duplicate_of_lead_id: UUID | None = None
    skill_used: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
