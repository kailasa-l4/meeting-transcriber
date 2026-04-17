import asyncio
import logging
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import WebSocket

from app.config import get_settings
from app.deepgram_streaming import DeepgramStreaming
from app.models import (
    ErrorMessage,
    SessionState,
    StatusUpdate,
    SummaryPosted,
    TranscriptUpdate,
)
from app.slack_client import (
    post_final_summary,
    post_meeting_header,
    post_threaded_summary,
    update_meeting_header,
    upload_audio_file,
)
from app.summarizer import cleanup_session, summarize_chunk, summarize_final
from app.database import add_summary, add_transcript, complete_meeting, create_meeting, update_meeting_slack_thread

logger = logging.getLogger(__name__)


@dataclass
class MeetingSession:
    session_id: str
    channel_id: str
    user_name: str
    client_ws: WebSocket
    deepgram: DeepgramStreaming | None = None
    state: SessionState = SessionState.STARTING
    slack_thread_ts: str = ""
    transcript_buffer: list[str] = field(default_factory=list)
    unsummarized_start: int = 0  # Index into transcript_buffer
    summaries: list[str] = field(default_factory=list)
    audio_chunks: list[bytes] = field(default_factory=list)
    summary_task: asyncio.Task | None = None
    start_time: float = 0.0
    last_summary_time: float = 0.0
    user_id: int = 0
    meeting_db_id: int | None = None


# Global session store
_sessions: dict[str, MeetingSession] = {}


async def _send_to_client(ws: WebSocket, message: dict) -> None:
    try:
        await ws.send_json(message)
    except Exception:
        logger.warning("Failed to send message to client WebSocket")


async def start_meeting(
    session_id: str,
    channel_id: str | None,
    user_name: str,
    user_id: int,
    client_ws: WebSocket,
) -> MeetingSession:
    settings = get_settings()
    channel = channel_id or settings.MEETING_CHANNEL_ID

    session = MeetingSession(
        session_id=session_id,
        channel_id=channel,
        user_name=user_name,
        client_ws=client_ws,
        start_time=time.time(),
        last_summary_time=time.time(),
    )
    _sessions[session_id] = session

    # Persist meeting to DB
    session.user_id = user_id
    meeting_db_id = await create_meeting(session_id, user_id, channel_id)
    session.meeting_db_id = meeting_db_id

    await _send_to_client(
        client_ws,
        StatusUpdate(state=SessionState.STARTING, message="Initializing...").model_dump(),
    )

    # Post Slack header
    try:
        session.slack_thread_ts = post_meeting_header(channel, user_name)
    except Exception:
        logger.exception("Failed to post Slack header")
        await _send_to_client(
            client_ws,
            ErrorMessage(message="Failed to post to Slack. Check bot token and channel.").model_dump(),
        )

    if session.slack_thread_ts and session.meeting_db_id:
        await update_meeting_slack_thread(session.meeting_db_id, session.slack_thread_ts)

    # Connect to Deepgram
    loop = asyncio.get_running_loop()

    def on_transcript(text: str, is_final: bool, speaker: int | None, start_time: float | None) -> None:
        loop.call_soon_threadsafe(
            asyncio.ensure_future,
            _handle_transcript(session, text, is_final, speaker, start_time),
        )

    session.deepgram = DeepgramStreaming(
        on_transcript=on_transcript,
        sample_rate=settings.AUDIO_SAMPLE_RATE,
    )
    await session.deepgram.connect()

    # Start periodic summary timer
    session.summary_task = asyncio.create_task(
        _summary_loop(session, settings.SUMMARY_INTERVAL_SECONDS)
    )

    session.state = SessionState.RECORDING
    await _send_to_client(
        client_ws,
        StatusUpdate(state=SessionState.RECORDING, message="Recording started").model_dump(),
    )

    logger.info("Meeting session %s started", session_id)
    return session


async def receive_audio(session_id: str, audio_chunk: bytes) -> None:
    session = _sessions.get(session_id)
    if session and session.deepgram and session.state == SessionState.RECORDING:
        session.audio_chunks.append(audio_chunk)
        await session.deepgram.send_audio(audio_chunk)


async def end_meeting(session_id: str) -> None:
    session = _sessions.get(session_id)
    if not session:
        return

    settings = get_settings()

    session.state = SessionState.STOPPING
    await _send_to_client(
        session.client_ws,
        StatusUpdate(state=SessionState.STOPPING, message="Generating final summary...").model_dump(),
    )

    # Stop summary loop
    if session.summary_task and not session.summary_task.done():
        session.summary_task.cancel()
        try:
            await session.summary_task
        except asyncio.CancelledError:
            pass

    # Close Deepgram
    if session.deepgram:
        await session.deepgram.close()

    # Generate and post final summary
    try:
        if session.summaries or session.transcript_buffer:
            final = await summarize_final(session_id, session.transcript_buffer, session.summaries)
            post_final_summary(session.channel_id, session.slack_thread_ts, final)

            if session.meeting_db_id and final:
                await add_summary(session.meeting_db_id, "final", final)

            await _send_to_client(
                session.client_ws,
                SummaryPosted(summary=final, time_range="Final").model_dump(),
            )

        # Update header
        duration = time.time() - session.start_time
        mins = int(duration // 60)
        duration_str = f"{mins}m" if mins > 0 else "<1m"
        update_meeting_header(
            session.channel_id, session.slack_thread_ts, duration_str
        )

        if session.meeting_db_id:
            title = session.summaries[0][:80] if session.summaries else f"Meeting {session.session_id}"
            await complete_meeting(session.meeting_db_id, int(duration), title)
    except Exception:
        logger.exception("Error generating final summary")

    # Write and upload meeting audio
    wav_path = None
    try:
        if session.audio_chunks:
            wav_path = Path("tmp") / f"meeting_{session_id}.wav"
            wav_path.parent.mkdir(exist_ok=True)
            with wave.open(str(wav_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(settings.AUDIO_SAMPLE_RATE)
                for chunk in session.audio_chunks:
                    wf.writeframes(chunk)
            logger.info("Wrote meeting audio: %s (%.1f MB)", wav_path, wav_path.stat().st_size / 1e6)

            upload_audio_file(
                channel=session.channel_id,
                thread_ts=session.slack_thread_ts,
                file_path=str(wav_path),
                title=f"Meeting Recording ({duration_str})",
            )
    except Exception:
        logger.exception("Error uploading meeting audio")
    finally:
        if wav_path and wav_path.exists():
            wav_path.unlink()
        session.audio_chunks.clear()

    session.state = SessionState.STOPPED
    await _send_to_client(
        session.client_ws,
        StatusUpdate(state=SessionState.STOPPED, message="Meeting ended").model_dump(),
    )

    cleanup_session(session_id)
    _sessions.pop(session_id, None)
    logger.info("Meeting session %s ended", session_id)


async def _handle_transcript(
    session: MeetingSession, text: str, is_final: bool,
    speaker: int | None = None, start_time: float | None = None,
) -> None:
    # Send to client for live display
    await _send_to_client(
        session.client_ws,
        TranscriptUpdate(
            text=text, is_final=is_final,
            speaker=speaker, timestamp=start_time,
        ).model_dump(),
    )

    # Only buffer final transcripts — include speaker label for summarizer context
    if is_final:
        prefix = f"[Speaker {speaker}] " if speaker is not None else ""
        session.transcript_buffer.append(f"{prefix}{text}")
        if session.meeting_db_id:
            await add_transcript(session.meeting_db_id, speaker, text, start_time)


async def _summary_loop(session: MeetingSession, interval: int) -> None:
    """Periodically summarize accumulated transcript and post to Slack."""
    try:
        while session.state == SessionState.RECORDING:
            await asyncio.sleep(interval)

            if session.state != SessionState.RECORDING:
                break

            # Get unsummarized transcript
            new_segments = session.transcript_buffer[session.unsummarized_start:]
            if not new_segments:
                continue

            new_text = " ".join(new_segments)
            session.unsummarized_start = len(session.transcript_buffer)

            # Build time range
            now = time.time()
            start_min = int((session.last_summary_time - session.start_time) // 60)
            end_min = int((now - session.start_time) // 60)
            time_range = f"{start_min}m - {end_min}m"
            session.last_summary_time = now

            try:
                summary = await summarize_chunk(session.session_id, new_text)
                session.summaries.append(summary)
                if session.meeting_db_id:
                    await add_summary(session.meeting_db_id, "chunk", summary, time_range)

                # Post to Slack thread
                if session.slack_thread_ts:
                    post_threaded_summary(
                        session.channel_id,
                        session.slack_thread_ts,
                        summary,
                        time_range,
                    )

                await _send_to_client(
                    session.client_ws,
                    SummaryPosted(summary=summary, time_range=time_range).model_dump(),
                )
            except Exception:
                logger.exception("Error in summary generation")

    except asyncio.CancelledError:
        pass


def get_session(session_id: str) -> MeetingSession | None:
    return _sessions.get(session_id)
