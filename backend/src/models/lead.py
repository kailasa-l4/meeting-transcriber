from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.enums import LeadVerificationStatus


class RawCandidate(BaseModel):
    """Pre-normalization lead candidate from discovery agents."""
    name: str | None = None
    role_title: str | None = None
    whatsapp: str | None = None
    phone: str | None = None
    details: str | None = None
    email: str | None = None
    company_name: str | None = None
    website: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    source_type: str | None = None
    source_excerpt: str | None = None
    discovery_skill: str | None = None


class NormalizedLead(BaseModel):
    """Normalized lead — the core schema every agent and route depends on."""
    name: str = Field(..., min_length=1, max_length=300)
    role_title: str | None = None
    whatsapp: str | None = None
    phone: str | None = None
    details: str | None = None
    email: str | None = None
    company_name: str | None = None
    website: str | None = None
    source_text: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    source_count: int = 0
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_breakdown: dict = Field(default_factory=dict)
    discovery_skill_used: str | None = None
    is_duplicate: bool = False
    duplicate_of: UUID | None = None

    @field_validator("phone", "whatsapp")
    @classmethod
    def strip_phone_formatting(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


class LeadResponse(BaseModel):
    """Full lead response for API."""
    id: UUID
    country_job_id: UUID
    name: str
    role_title: str | None = None
    whatsapp: str | None = None
    phone: str | None = None
    details: str | None = None
    email: str | None = None
    company_name: str | None = None
    website: str | None = None
    source_text: str | None = None
    source_urls: list[str] = []
    source_count: int = 0
    verification_status: LeadVerificationStatus
    confidence_score: float
    confidence_breakdown: dict = {}
    discovery_skill_used: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadSourceResponse(BaseModel):
    """Lead source evidence."""
    id: UUID
    lead_id: UUID
    source_url: str | None = None
    source_title: str | None = None
    source_type: str | None = None
    excerpt: str | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadDetailResponse(BaseModel):
    """Full lead detail with sources and verification."""
    lead: LeadResponse
    sources: list[LeadSourceResponse] = []
    verification_records: list["VerificationRecordResponse"] = []
    draft_status: str | None = None


# Forward reference resolved at module level
from src.models.verification import VerificationRecordResponse  # noqa: E402
LeadDetailResponse.model_rebuild()
