from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import KnowledgeType


class CountryKnowledgeEntry(BaseModel):
    """A knowledge entry for a country."""
    country: str
    knowledge_type: KnowledgeType
    content: dict
    source: str | None = None


class CountryKnowledgeResponse(BaseModel):
    """Knowledge entry for API response."""
    id: UUID
    country: str
    knowledge_type: KnowledgeType
    content: dict
    source: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
