"""Discovery Planning step -- derives research lanes from user context."""

from sqlalchemy.orm import Session

from src.db.models import CountryJob, WorkflowEvent

# Default target types when user doesn't specify
DEFAULT_TARGET_TYPES = ["miners", "brokers", "exporters", "refiners", "dealers"]
DEFAULT_REGIONS = ["capital", "mining_regions"]


def run_discovery_planning(state: dict, db: Session) -> dict:
    """Build a discovery plan from user context and stored knowledge."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.current_stage = "discovery_planning"

    user_ctx = state.get("user_context", {})
    merged = state.get("merged_context", {})

    target_types = user_ctx.get("target_types") or DEFAULT_TARGET_TYPES
    regions = user_ctx.get("regions") or DEFAULT_REGIONS
    known_entities = user_ctx.get("known_entities", [])
    exclusions = user_ctx.get("exclusions", [])

    # Build research lanes -- one per target type
    lanes = []
    for target in target_types:
        lane = {
            "target_type": target,
            "country": state["country"],
            "regions": regions,
            "exclusions": exclusions,
        }
        # Pull relevant knowledge if available
        stored = merged.get("stored_knowledge", {})
        if "search_strategy" in stored:
            lane["search_hints"] = stored["search_strategy"]
        if "directory" in stored:
            lane["known_directories"] = stored["directory"]
        lanes.append(lane)

    plan = {
        "country": state["country"],
        "lanes": lanes,
        "known_entities": known_entities,
        "exclusions": exclusions,
        "total_lanes": len(lanes),
    }

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="discovery_planned",
        stage="discovery_planning",
        payload={
            "lane_count": len(lanes),
            "target_types": target_types,
            "regions": regions,
        },
    )
    db.add(event)
    db.commit()

    state["discovery_plan"] = plan
    return state
