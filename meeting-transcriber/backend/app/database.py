"""SQLAlchemy async persistence layer.

Public functions return plain dicts (or lists of dicts) so callers in main.py
and auth.py don't need to know about ORM instances.
"""

import logging
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models_db import Meeting, Summary, Transcript, Transcription, User

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


def _to_dict(row: Any) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict."""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def _session() -> AsyncSession:
    assert _SessionLocal is not None, "init_db not called"
    return _SessionLocal()


async def init_db() -> None:
    """Initialize the async engine and session factory. Called on app startup.

    Migrations are applied separately by `alembic upgrade head` (entrypoint.sh).
    """
    global _engine, _SessionLocal
    settings = get_settings()
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database engine initialized")


async def dispose_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


# -- User CRUD --

async def create_user(username: str, password_hash: str, display_name: str) -> int:
    async with _session() as s:
        user = User(username=username, password_hash=password_hash, display_name=display_name)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user.id


async def get_user_by_username(username: str) -> dict | None:
    async with _session() as s:
        result = await s.execute(select(User).where(User.username == username))
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with _session() as s:
        row = await s.get(User, user_id)
        if not row:
            return None
        d = _to_dict(row)
        d.pop("password_hash", None)
        return d


async def list_users(status_filter: str | None = None) -> list[dict]:
    async with _session() as s:
        stmt = select(User)
        if status_filter:
            stmt = stmt.where(User.status == status_filter)
        else:
            stmt = stmt.where(User.status != "deleted")
        stmt = stmt.order_by(User.created_at.desc())
        result = await s.execute(stmt)
        rows = result.scalars().all()
        out = []
        for r in rows:
            d = _to_dict(r)
            d.pop("password_hash", None)
            d.pop("approved_by", None)
            out.append(d)
        return out


async def set_user_status(user_id: int, status: str, approved_by: int | None = None) -> None:
    async with _session() as s:
        if status == "approved":
            await s.execute(
                update(User)
                .where(User.id == user_id)
                .values(status=status, approved_at=func.now(), approved_by=approved_by)
            )
        else:
            await s.execute(update(User).where(User.id == user_id).values(status=status))
        await s.commit()


async def soft_delete_user(user_id: int) -> None:
    """Soft delete: rename username to free it; mark status='deleted'. Data preserved."""
    async with _session() as s:
        row = await s.get(User, user_id)
        if not row:
            return
        original = row.username
        suffix = f"__deleted_{user_id}"
        new_username = original if original.endswith(suffix) else f"{original}{suffix}"
        row.username = new_username
        row.status = "deleted"
        await s.commit()


# -- Meeting CRUD --

async def create_meeting(session_id: str, user_id: int, channel_id: str | None) -> int:
    async with _session() as s:
        m = Meeting(session_id=session_id, user_id=user_id, channel_id=channel_id)
        s.add(m)
        await s.commit()
        await s.refresh(m)
        return m.id


async def complete_meeting(meeting_id: int, duration_seconds: int, title: str | None = None) -> None:
    async with _session() as s:
        await s.execute(
            update(Meeting)
            .where(Meeting.id == meeting_id)
            .values(status="completed", duration_seconds=duration_seconds, title=title, ended_at=func.now())
        )
        await s.commit()


async def update_meeting_slack_thread(meeting_id: int, slack_thread_ts: str) -> None:
    async with _session() as s:
        await s.execute(
            update(Meeting).where(Meeting.id == meeting_id).values(slack_thread_ts=slack_thread_ts)
        )
        await s.commit()


async def get_meetings_for_user(user_id: int) -> list[dict]:
    async with _session() as s:
        stmt = (
            select(Meeting.id, Meeting.session_id, Meeting.title, Meeting.status,
                   Meeting.duration_seconds, Meeting.started_at, Meeting.ended_at)
            .where(Meeting.user_id == user_id)
            .order_by(Meeting.started_at.desc())
        )
        result = await s.execute(stmt)
        return [dict(r._mapping) for r in result.all()]


async def get_meeting_by_id(meeting_id: int, user_id: int) -> dict | None:
    async with _session() as s:
        result = await s.execute(
            select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


# -- Transcript CRUD --

async def add_transcript(meeting_id: int, speaker: int | None, text: str, timestamp: float | None) -> None:
    async with _session() as s:
        s.add(Transcript(meeting_id=meeting_id, speaker=speaker, text=text, timestamp=timestamp))
        await s.commit()


async def get_transcripts(meeting_id: int) -> list[dict]:
    async with _session() as s:
        stmt = (
            select(Transcript.speaker, Transcript.text, Transcript.timestamp)
            .where(Transcript.meeting_id == meeting_id)
            .order_by(Transcript.id)
        )
        result = await s.execute(stmt)
        return [dict(r._mapping) for r in result.all()]


# -- Summary CRUD --

async def add_summary(meeting_id: int, summary_type: str, content: str, time_range: str | None = None) -> None:
    async with _session() as s:
        s.add(Summary(meeting_id=meeting_id, type=summary_type, content=content, time_range=time_range))
        await s.commit()


async def get_summaries(meeting_id: int) -> list[dict]:
    async with _session() as s:
        stmt = (
            select(Summary.type, Summary.content, Summary.time_range, Summary.created_at)
            .where(Summary.meeting_id == meeting_id)
            .order_by(Summary.id)
        )
        result = await s.execute(stmt)
        return [dict(r._mapping) for r in result.all()]


# -- Transcription CRUD --

async def create_transcription(user_id: int, file_name: str) -> int:
    async with _session() as s:
        t = Transcription(user_id=user_id, file_name=file_name)
        s.add(t)
        await s.commit()
        await s.refresh(t)
        return t.id


async def complete_transcription(
    transcription_id: int, transcript: str, segments: str, duration_seconds: int | None
) -> None:
    async with _session() as s:
        await s.execute(
            update(Transcription)
            .where(Transcription.id == transcription_id)
            .values(
                status="completed",
                transcript=transcript,
                segments=segments,
                duration_seconds=duration_seconds,
                completed_at=func.now(),
            )
        )
        await s.commit()


async def fail_transcription(transcription_id: int, error_message: str) -> None:
    async with _session() as s:
        await s.execute(
            update(Transcription)
            .where(Transcription.id == transcription_id)
            .values(status="failed", error_message=error_message, completed_at=func.now())
        )
        await s.commit()


async def get_transcription(transcription_id: int, user_id: int) -> dict | None:
    async with _session() as s:
        result = await s.execute(
            select(Transcription).where(
                Transcription.id == transcription_id,
                Transcription.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


async def get_transcriptions_for_user(user_id: int) -> list[dict]:
    async with _session() as s:
        stmt = (
            select(
                Transcription.id, Transcription.file_name, Transcription.status,
                Transcription.duration_seconds, Transcription.created_at, Transcription.completed_at,
            )
            .where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
        )
        result = await s.execute(stmt)
        return [dict(r._mapping) for r in result.all()]
