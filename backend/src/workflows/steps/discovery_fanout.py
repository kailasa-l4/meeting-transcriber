"""Discovery Fan-out step -- calls OpenRouter directly for structured lead research."""

import json
import httpx

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, WorkflowEvent
from src.config import settings


DISCOVERY_PROMPT = """You are a gold industry lead researcher. Find real gold-related companies, contacts, and organizations in {country}.

Research these categories: {target_types}
{regions_note}
{known_entities_note}
{exclusions_note}

Return ONLY a JSON array of leads. Each lead must have these fields:
- "name": contact person name (or company name if no person known)
- "company_name": organization name
- "role_title": job title or role
- "email": email address (use realistic format like info@company.com if exact unknown)
- "phone": phone number with country code
- "website": company website URL
- "details": 1-2 sentence description of what they do in gold
- "source_text": where this information might be found
- "whatsapp": WhatsApp number if different from phone

Find at least 8-12 leads across the categories. Focus on REAL companies that are known to operate in {country}'s gold sector.

IMPORTANT: Return ONLY the JSON array, no other text."""


def run_discovery_fanout(state: dict, db: Session) -> dict:
    """Call OpenRouter directly to discover gold leads with structured JSON output."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.status = CountryJobStatus.running
    job.current_stage = "discovery_fanout"
    db.commit()

    plan = state.get("discovery_plan", {})
    country = state["country"]
    user_ctx = state.get("user_context", {})

    target_types = ", ".join(
        lane.get("target_type", "")
        for lane in plan.get("lanes", [{"target_type": "miners"}, {"target_type": "brokers"}, {"target_type": "exporters"}, {"target_type": "refiners"}, {"target_type": "associations"}])
    )

    regions_note = ""
    if user_ctx.get("regions"):
        regions_note = f"Focus on these regions: {', '.join(user_ctx['regions'])}"

    known_note = ""
    if user_ctx.get("known_entities"):
        known_note = f"Include these known entities: {', '.join(user_ctx['known_entities'])}"

    exclusions_note = ""
    if state.get("exclusion_emails") or state.get("exclusion_companies"):
        exclusions_note = f"Exclude: {', '.join(state.get('exclusion_companies', []))}"

    prompt = DISCOVERY_PROMPT.format(
        country=country,
        target_types=target_types,
        regions_note=regions_note,
        known_entities_note=known_note,
        exclusions_note=exclusions_note,
    )

    # Direct OpenRouter call for structured output
    raw_candidates = []
    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshotai/kimi-k2.5",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8000,
                "temperature": 0.7,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("choices", [{}])[0].get("message", {})
        # Kimi K2.5 is a reasoning model — content may be null, check reasoning field too
        content = msg.get("content") or msg.get("reasoning") or ""

        # Extract JSON array from response
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            parsed = json.loads(content[start : end + 1])
            if isinstance(parsed, list):
                raw_candidates = parsed

        # Track token usage
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        if total_tokens:
            job.total_token_count = (job.total_token_count or 0) + total_tokens

    except Exception as exc:
        # Store error but continue pipeline
        event = WorkflowEvent(
            country_job_id=job.id,
            event_type="discovery_error",
            stage="discovery_fanout",
            payload={"error": str(exc)},
        )
        db.add(event)

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="discovery_completed",
        stage="discovery_fanout",
        payload={"candidates_found": len(raw_candidates)},
    )
    db.add(event)
    db.commit()

    # Pass structured candidates directly (skip text parsing in normalization)
    state["raw_candidates"] = [{"parsed_leads": raw_candidates, "country": country}]
    return state
