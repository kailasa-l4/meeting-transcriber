"""Token usage and cost tracking per session."""
import logging
from sqlalchemy.orm import Session
from src.db.models import CountryJob, WorkflowEvent

logger = logging.getLogger(__name__)

# Approximate cost per 1M tokens for common models
MODEL_COSTS_PER_1M = {
    "moonshotai/kimi-k2.5": {"input": 0.50, "output": 1.50},
    "default": {"input": 1.00, "output": 3.00},
}


def track_token_usage(
    db: Session,
    job_id: str,
    token_count: int,
    stage: str,
    model_name: str = "default",
):
    """Record token usage for a workflow stage and update job totals."""
    # Update job totals
    job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
    if job:
        job.total_token_count = (job.total_token_count or 0) + token_count
        costs = MODEL_COSTS_PER_1M.get(model_name, MODEL_COSTS_PER_1M["default"])
        estimated_cost = (token_count / 1_000_000) * (costs["input"] + costs["output"]) / 2
        job.estimated_cost = (job.estimated_cost or 0.0) + estimated_cost

    # Create workflow event
    event = WorkflowEvent(
        country_job_id=job_id,
        event_type="token_usage",
        stage=stage,
        token_count=token_count,
        payload={"model": model_name, "tokens": token_count},
    )
    db.add(event)
    db.flush()


def get_session_cost_summary(db: Session, job_id: str) -> dict:
    """Get cost summary for a session."""
    job = db.query(CountryJob).filter(CountryJob.id == job_id).first()
    if not job:
        return {"error": "Job not found"}

    return {
        "job_id": str(job.id),
        "total_tokens": job.total_token_count or 0,
        "estimated_cost_usd": round(job.estimated_cost or 0.0, 4),
        "country": job.country,
        "status": job.status.value if job.status else None,
    }
