from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SkillInvocationLogResponse(BaseModel):
    """Skill invocation log for API response."""
    id: UUID
    country_job_id: UUID
    skill_name: str
    skill_version: str | None = None
    agent_name: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    token_count: int = 0
    duration_ms: int = 0
    status: str
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
