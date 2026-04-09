"""Knowledge Seeding step -- loads country knowledge from DB and merges with user context."""

from sqlalchemy.orm import Session

from src.db.models import CountryJob, CountryJobStatus, CountryKnowledge, WorkflowEvent


def run_knowledge_seeding(state: dict, db: Session) -> dict:
    """Load existing country knowledge and merge with user-supplied context."""
    job = db.query(CountryJob).filter(CountryJob.id == state["job_id"]).first()
    job.status = CountryJobStatus.seeding_knowledge
    job.current_stage = "knowledge_seeding"

    # Load all knowledge entries for this country
    knowledge_entries = (
        db.query(CountryKnowledge)
        .filter(CountryKnowledge.country.ilike(f"%{state['country']}%"))
        .all()
    )

    knowledge_map = {}
    for entry in knowledge_entries:
        k_type = entry.knowledge_type.value if hasattr(entry.knowledge_type, "value") else str(entry.knowledge_type)
        if k_type not in knowledge_map:
            knowledge_map[k_type] = []
        knowledge_map[k_type].append(entry.content)

    # Merge user context with stored knowledge
    merged_context = {
        **state.get("user_context", {}),
        "stored_knowledge": knowledge_map,
        "knowledge_entry_count": len(knowledge_entries),
    }

    event = WorkflowEvent(
        country_job_id=job.id,
        event_type="knowledge_seeded",
        stage="knowledge_seeding",
        payload={
            "entries_loaded": len(knowledge_entries),
            "knowledge_types": list(knowledge_map.keys()),
        },
    )
    db.add(event)
    db.commit()

    state["merged_context"] = merged_context
    return state
