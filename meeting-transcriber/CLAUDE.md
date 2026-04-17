# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install dependencies
cd backend && uv sync

# Run locally (MUST exclude .venv or reload loops crash active sessions)
uv run uvicorn app.main:app --reload --reload-exclude .venv --port 8000

# Expose via HTTPS tunnel (required for mobile mic access)
cloudflared tunnel --url http://localhost:8000

# Docker (exposes port 8001)
docker compose up --build
```

No test suite exists yet. Verify manually: open the frontend, start a meeting, check Slack thread.

## Architecture

Real-time meeting transcription PWA: browser captures mic audio, streams to backend via WebSocket, backend pipes to Deepgram for transcription, Agno agents summarize periodically, results post to a Slack thread.

```
Browser (AudioWorklet PCM 16kHz)
  → WebSocket (binary audio + JSON control)
    → FastAPI main.py routes to session_manager.py
      → deepgram_streaming.py (Nova-3 streaming WS, diarize=true)
      → summarizer.py (Agno agents via OpenRouter)
      → slack_client.py (threaded messages + audio upload)
```

### Data flow for audio

1. `audio-capture.js` → `getUserMedia` mono 16kHz → `AudioWorklet`
2. `audio-processor.worklet.js` converts Float32 → Int16 PCM, posts 4096-sample chunks
3. `ws-client.js` sends binary frames to `/ws/meeting/{session_id}`
4. `session_manager.py` buffers chunks in `audio_chunks` AND forwards to Deepgram
5. On meeting end: `wave` stdlib writes WAV from raw PCM, uploads to Slack, deletes temp file

### Dual-model Agno agents (summarizer.py)

- **Chunk agent** (one per meeting session): fast model (`CHUNK_MODEL`), `add_history_to_context=True` with `SqliteDb`. Every 3 min, receives new transcript; Agno auto-injects all prior chunks+summaries as context. Produces short bullet-point notes.
- **Final agent** (stateless): powerful model (`FINAL_MODEL`), receives all interim summaries + remaining transcript in a single call. Produces comprehensive recap.
- Agent instances cleaned up in `cleanup_session()` on meeting end.
- Session history persists in `tmp/meeting_sessions.db` (SQLite).

### Slack threading pattern (slack_client.py)

Meeting start → `post_meeting_header()` returns `thread_ts` → periodic `post_threaded_summary()` → meeting end: `post_final_summary()` (auto-splits at 2900 chars for Slack's 3000 limit) + `upload_audio_file()` + `update_meeting_header()`.

### Frontend isolation

`audio-capture.js` is the only file that touches browser audio APIs. Designed for drop-in replacement with a Capacitor native plugin for true background recording. Everything else communicates through `startCapture(onChunk)` / `stopCapture()`.

## Key Patterns

**Deepgram callback threading**: The `on_transcript` callback runs in websockets' thread. Must use `loop.call_soon_threadsafe(asyncio.ensure_future, ...)` to marshal back to the async event loop.

**Speaker diarization**: `diarize=true` in Deepgram params. Dominant speaker per segment = most frequent `speaker` int in the word-level array. Frontend color-codes with `SPEAKER_COLORS[speaker % 6]`.

**WebSocket stop flow**: Client sends `stop_meeting` JSON, server generates final summary + uploads audio, then sends `status: "stopped"`. Frontend waits for this status before disconnecting — no timers.

## Gotchas

- **websockets v14+**: Uses `from websockets.protocol import State as WsState` and `ws.state == WsState.OPEN`. Older versions had `.open` property — will crash.
- **Slack scopes**: Bot needs `chat:write` + `files:write`. Missing `files:write` = audio upload fails silently in the error handler.
- **Slack block limit**: Section text max 3000 chars. `_split_text_blocks()` handles this for final summaries.
- **Transcript buffer includes speaker**: Entries are `[Speaker N] text` so the LLM summarizer gets speaker context.
- **OPENROUTER_API_KEY**: Set both in `.env` and as `os.environ` (summarizer.py does `setdefault`) because Agno's OpenRouter model reads from env.
