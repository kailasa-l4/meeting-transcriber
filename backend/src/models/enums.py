import enum


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


class StructuredFeedbackCategory(str, enum.Enum):
    tone_adjustment = "tone_adjustment"
    missing_information = "missing_information"
    factual_error = "factual_error"
    length_issue = "length_issue"
    wrong_template = "wrong_template"
    personalization_needed = "personalization_needed"
    other = "other"
