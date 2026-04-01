"""Country Research Workflow -- Agno Workflow orchestrating the 12-stage pipeline.

Uses Agno's Workflow + Step with custom executor functions. Each step wraps
a plain-function step module from src.workflows.steps, giving us testable
units that also plug into Agno's session tracking and HITL confirmation.
"""

from agno.workflow import OnReject
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

from src.db.base import SessionLocal


# ---------------------------------------------------------------------------
# Step executor wrappers
#
# Each Agno Step executor receives StepInput and returns StepOutput.
# Internally they open a DB session and delegate to the plain-function step.
# The workflow state is threaded through StepInput.previous_step_content as
# JSON, so each step can deserialize, mutate, and re-serialize.
# ---------------------------------------------------------------------------

import json
from typing import Any


def _load_state(step_input: StepInput) -> dict:
    """Deserialize workflow state from previous step content or initial input."""
    raw = step_input.previous_step_content or step_input.input or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"raw_input": str(raw)}


def _to_output(state: dict) -> StepOutput:
    """Serialize workflow state into a StepOutput."""
    return StepOutput(content=json.dumps(state, default=str))


# --- Individual executors ---


def intake_executor(step_input: StepInput) -> StepOutput:
    """Create a CountryJob and initialize state."""
    from src.workflows.steps.intake import run_intake
    from src.models.country_job import CountrySubmissionInput

    raw = step_input.input or "{}"
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"country": raw}
    else:
        data = raw

    input_model = CountrySubmissionInput(**data)
    db = SessionLocal()
    try:
        state = run_intake(input_model, db)
        return _to_output(state)
    finally:
        db.close()


def knowledge_seeding_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.knowledge_seeding import run_knowledge_seeding

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_knowledge_seeding(state, db)
        return _to_output(state)
    finally:
        db.close()


def discovery_planning_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.discovery_planning import run_discovery_planning

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_discovery_planning(state, db)
        return _to_output(state)
    finally:
        db.close()


def discovery_fanout_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.discovery_fanout import run_discovery_fanout

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_discovery_fanout(state, db)
        return _to_output(state)
    finally:
        db.close()


def normalization_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.normalization import run_normalization

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_normalization(state, db)
        return _to_output(state)
    finally:
        db.close()


def verification_fanout_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.verification_fanout import run_verification_fanout

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_verification_fanout(state, db)
        return _to_output(state)
    finally:
        db.close()


def lead_persistence_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.lead_persistence import run_lead_persistence

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_lead_persistence(state, db)
        return _to_output(state)
    finally:
        db.close()


def draft_generation_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.draft_generation import run_draft_generation

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_draft_generation(state, db)
        return _to_output(state)
    finally:
        db.close()


def approval_wait_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.approval_wait import run_approval_wait

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_approval_wait(state, db)
        return _to_output(state)
    finally:
        db.close()


def final_send_executor(step_input: StepInput) -> StepOutput:
    from src.workflows.steps.final_send import run_final_send

    state = _load_state(step_input)
    db = SessionLocal()
    try:
        state = run_final_send(state, db)
        return _to_output(state)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------

country_research_workflow = Workflow(
    name="Country Research Workflow",
    description="End-to-end gold lead discovery, verification, and outreach pipeline",
    steps=[
        Step(name="intake", executor=intake_executor),
        Step(name="knowledge_seeding", executor=knowledge_seeding_executor),
        Step(name="discovery_planning", executor=discovery_planning_executor),
        Step(name="discovery_fanout", executor=discovery_fanout_executor),
        Step(name="normalization", executor=normalization_executor),
        Step(name="verification_fanout", executor=verification_fanout_executor),
        Step(name="lead_persistence", executor=lead_persistence_executor),
        Step(name="draft_generation", executor=draft_generation_executor),
        Step(
            name="approval_wait",
            executor=approval_wait_executor,
            requires_confirmation=True,
            confirmation_message=(
                "Drafts are ready for review. Approve to proceed to sending, "
                "or reject to skip sending."
            ),
            on_reject=OnReject.skip,
        ),
        Step(name="final_send", executor=final_send_executor),
    ],
)


# Convenience alias
CountryResearchWorkflow = country_research_workflow
