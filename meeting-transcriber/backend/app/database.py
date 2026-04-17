"""Persistent SQLite database for users, meetings, transcripts, and summaries."""

import aiosqlite
import logging
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

_db_path: str = ""


async def init_db() -> None:
    """Create tables if they don't exist. Called on app startup."""
    global _db_path
    settings = get_settings()
    _db_path = settings.DB_PATH

    # Ensure parent directory exists
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(_db_path) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name  TEXT NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS meetings (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id       TEXT UNIQUE NOT NULL,
                user_id          INTEGER NOT NULL REFERENCES users(id),
                title            TEXT,
                channel_id       TEXT,
                slack_thread_ts  TEXT,
                status           TEXT DEFAULT 'recording',
                duration_seconds INTEGER,
                started_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at         TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL REFERENCES meetings(id),
                speaker    INTEGER,
                text       TEXT NOT NULL,
                timestamp  REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS summaries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL REFERENCES meetings(id),
                type       TEXT NOT NULL,
                content    TEXT NOT NULL,
                time_range TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transcriptions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL REFERENCES users(id),
                file_name        TEXT NOT NULL,
                duration_seconds INTEGER,
                status           TEXT DEFAULT 'processing',
                transcript       TEXT,
                segments         TEXT,
                error_message    TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at     TIMESTAMP
            );
        """)
        await db.commit()
    logger.info("Database initialized at %s", _db_path)


def _get_db_path() -> str:
    return _db_path


# -- User CRUD --

async def create_user(username: str, password_hash: str, display_name: str) -> int:
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
            (username, password_hash, display_name),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_by_username(username: str) -> dict | None:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, username, display_name, created_at FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# -- Meeting CRUD --

async def create_meeting(session_id: str, user_id: int, channel_id: str | None) -> int:
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            "INSERT INTO meetings (session_id, user_id, channel_id) VALUES (?, ?, ?)",
            (session_id, user_id, channel_id),
        )
        await db.commit()
        return cursor.lastrowid


async def complete_meeting(meeting_id: int, duration_seconds: int, title: str | None = None) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "UPDATE meetings SET status = 'completed', duration_seconds = ?, title = ?, ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (duration_seconds, title, meeting_id),
        )
        await db.commit()


async def update_meeting_slack_thread(meeting_id: int, slack_thread_ts: str) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "UPDATE meetings SET slack_thread_ts = ? WHERE id = ?",
            (slack_thread_ts, meeting_id),
        )
        await db.commit()


async def get_meetings_for_user(user_id: int) -> list[dict]:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, session_id, title, status, duration_seconds, started_at, ended_at FROM meetings WHERE user_id = ? ORDER BY started_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_meeting_by_id(meeting_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM meetings WHERE id = ? AND user_id = ?",
            (meeting_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# -- Transcript CRUD --

async def add_transcript(meeting_id: int, speaker: int | None, text: str, timestamp: float | None) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "INSERT INTO transcripts (meeting_id, speaker, text, timestamp) VALUES (?, ?, ?, ?)",
            (meeting_id, speaker, text, timestamp),
        )
        await db.commit()


async def get_transcripts(meeting_id: int) -> list[dict]:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT speaker, text, timestamp FROM transcripts WHERE meeting_id = ? ORDER BY id",
            (meeting_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# -- Summary CRUD --

async def add_summary(meeting_id: int, summary_type: str, content: str, time_range: str | None = None) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "INSERT INTO summaries (meeting_id, type, content, time_range) VALUES (?, ?, ?, ?)",
            (meeting_id, summary_type, content, time_range),
        )
        await db.commit()


async def get_summaries(meeting_id: int) -> list[dict]:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT type, content, time_range, created_at FROM summaries WHERE meeting_id = ? ORDER BY id",
            (meeting_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# -- Transcription CRUD --

async def create_transcription(user_id: int, file_name: str) -> int:
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            "INSERT INTO transcriptions (user_id, file_name) VALUES (?, ?)",
            (user_id, file_name),
        )
        await db.commit()
        return cursor.lastrowid


async def complete_transcription(transcription_id: int, transcript: str, segments: str, duration_seconds: int | None) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "UPDATE transcriptions SET status = 'completed', transcript = ?, segments = ?, duration_seconds = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (transcript, segments, duration_seconds, transcription_id),
        )
        await db.commit()


async def fail_transcription(transcription_id: int, error_message: str) -> None:
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "UPDATE transcriptions SET status = 'failed', error_message = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (error_message, transcription_id),
        )
        await db.commit()


async def get_transcription(transcription_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_transcriptions_for_user(user_id: int) -> list[dict]:
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, file_name, status, duration_seconds, created_at, completed_at FROM transcriptions WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
