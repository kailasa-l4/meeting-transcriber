import logging
import os

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter

from app.config import get_settings

logger = logging.getLogger(__name__)

CHUNK_INSTRUCTIONS = (
    "You are a quick meeting note-taker. You receive a short transcript chunk from an "
    "ongoing meeting every few minutes. Your conversation history has all prior chunks "
    "and notes — use that context to be smart, but keep your output SHORT.\n\n"
    "Output rules:\n"
    "• Write 2-5 bullet points MAX — just the essentials from this chunk\n"
    "• Each bullet: one line, plain language, no fluff\n"
    "• If something connects to an earlier topic, mention it briefly "
    "(e.g., 'Revisited X — now leaning toward Y')\n"
    "• Only note a decision or action item if one was explicitly stated\n"
    "• Do NOT use section headers — just bullets\n"
    "• Do NOT repeat anything from previous notes\n"
    "• Use Slack mrkdwn: *bold* for names/decisions, _ for emphasis\n"
    "• If the chunk is mostly filler/small talk, write 1-2 bullets or just 'General discussion, no key points.'\n\n"
    "Think quick status update, not meeting minutes. Aim for under 100 words."
)

FINAL_INSTRUCTIONS = (
    "You are writing the final comprehensive summary of a completed meeting. "
    "You receive all interim summaries and any remaining un-summarized transcript. "
    "Produce a thorough meeting recap:\n\n"
    "1) *Meeting Overview* (2-3 sentences capturing the essence)\n"
    "2) *Key Decisions* — what was decided and any context\n"
    "3) *Action Items* — with owners and deadlines if mentioned\n"
    "4) *Open Questions / Follow-ups* — unresolved items\n"
    "5) *Notable Discussion Points* — important context and nuances\n\n"
    "Guidelines:\n"
    "• Synthesize — don't just concatenate the interim summaries\n"
    "• Highlight how discussions evolved throughout the meeting\n"
    "• Use Slack mrkdwn formatting (* for bold, _ for italic, • for bullets)\n"
    "• Omit empty sections"
)

# Agent storage for session history (shared Postgres; Agno uses psycopg sync driver).
# The app's DATABASE_URL is `postgresql+asyncpg://…` for SQLAlchemy async; strip
# the `+asyncpg` suffix so Agno's psycopg driver parses it correctly.
def _agno_db_url() -> str:
    url = os.environ.get("DATABASE_URL") or get_settings().DATABASE_URL
    # App uses `postgresql+asyncpg://` for SQLAlchemy async; Agno uses psycopg3 sync,
    # so swap the driver suffix to `+psycopg` (SQLAlchemy's psycopg3 dialect name).
    return url.replace("+asyncpg", "+psycopg")


_db = PostgresDb(db_url=_agno_db_url())

# Per-session chunk agents (each meeting gets its own agent instance with history)
_chunk_agents: dict[str, Agent] = {}


def _get_chunk_agent(session_id: str) -> Agent:
    """Get or create a chunk summary agent for this meeting session."""
    if session_id not in _chunk_agents:
        settings = get_settings()
        os.environ.setdefault("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY)

        _chunk_agents[session_id] = Agent(
            model=OpenRouter(id=settings.CHUNK_MODEL),
            instructions=CHUNK_INSTRUCTIONS,
            db=_db,
            add_history_to_context=True,
            markdown=True,
        )

    return _chunk_agents[session_id]


def _get_final_agent() -> Agent:
    """Create a final summary agent (no history needed — gets everything in one call)."""
    settings = get_settings()
    os.environ.setdefault("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY)

    return Agent(
        model=OpenRouter(id=settings.FINAL_MODEL),
        instructions=FINAL_INSTRUCTIONS,
        markdown=True,
    )


async def summarize_chunk(session_id: str, new_transcript: str) -> str:
    """
    Summarize a new transcript chunk with full meeting context.

    The Agno agent automatically includes all previous conversation turns
    (transcript chunks + summaries) via add_history_to_context=True,
    so each summary is contextually aware of the entire meeting so far.
    """
    agent = _get_chunk_agent(session_id)

    message = f"New transcript chunk from the meeting:\n\n{new_transcript}"

    result = await agent.arun(message, session_id=session_id)
    summary = result.content

    logger.info("Generated chunk summary: %d characters", len(summary))
    return summary


async def summarize_final(
    session_id: str, full_transcript: list[str], all_summaries: list[str],
) -> str:
    """Generate the final comprehensive meeting summary from the full transcript."""
    agent = _get_final_agent()

    user_content = "Here is the full meeting transcript:\n\n"
    user_content += "\n".join(full_transcript)
    user_content += "\n\n---\n\nHere are the interim summaries produced during the meeting for additional context:\n\n"
    for i, s in enumerate(all_summaries, 1):
        user_content += f"--- Summary {i} ---\n{s}\n\n"

    result = await agent.arun(user_content)
    summary = result.content

    logger.info("Generated final summary: %d characters", len(summary))
    return summary


def cleanup_session(session_id: str) -> None:
    """Clean up agent instance for a completed meeting."""
    _chunk_agents.pop(session_id, None)
