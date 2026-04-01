"""Discovery Fan-out step -- runs the discovery team to collect raw candidates."""

import json

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, WorkflowEvent


def run_discovery_fanout(state: dict, db: Session) -> dict:
    """Run the discovery team against the planned lanes and collect candidates."""
    from src.teams.discovery_team import discovery_team

    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.status = CountryJobStatus.running
    job.current_stage = "discovery_fanout"
    db.commit()

    plan = state.get("discovery_plan", {})
    country = state["country"]

    # Build the prompt for the discovery team
    prompt = (
        f"Discover gold-related leads in {country}.\n\n"
        f"Research Plan:\n{json.dumps(plan, indent=2, default=str)}\n\n"
        f"Find contacts for the following target types: "
        f"{', '.join(lane['target_type'] for lane in plan.get('lanes', []))}.\n"
        f"Focus on entities with verifiable contact information."
    )

    if plan.get("known_entities"):
        prompt += f"\n\nKnown entities to expand upon: {', '.join(plan['known_entities'])}"
    if plan.get("exclusions"):
        prompt += f"\n\nExclude: {', '.join(plan['exclusions'])}"

    # Run the discovery team
    response = discovery_team.run(prompt)

    # Extract raw candidates from team response
    raw_candidates = []
    if response and response.content:
        raw_candidates.append({
            "raw_text": response.content,
            "source": "discovery_team",
            "country": country,
        })

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="discovery_completed",
        stage="discovery_fanout",
        payload={
            "raw_candidate_batches": len(raw_candidates),
        },
    )
    db.add(event)
    db.commit()

    state["raw_candidates"] = raw_candidates
    return state
