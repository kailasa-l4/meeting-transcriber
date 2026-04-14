# Meeting Transcriber: Persistent DB, Multi-User Support & New UI

## Context

The meeting transcriber currently stores all data temporarily (in-memory session dict + Agno's SQLite for agent history in `tmp/`). It supports only one user at a time, and previous meeting sessions are lost after the server restarts. The frontend is vanilla JS with no session history browsing.

**Goal:** Add persistent storage, multi-user authentication, and a modern mobile-first UI that lets users browse their past meetings with full transcripts and summaries.

## Architecture

Two-process architecture:

- **TanStack Start** (React frontend) — routing, auth UI, meeting views, Shadcn components
- **FastAPI** (Python backend) — WebSocket audio streaming, Deepgram, Agno summarization, Slack, persistent SQLite DB

```
TanStack Start (Vite dev: port 3000)
  ├── /login, /register — auth pages
  ├── / — dashboard (sidebar + active meeting)
  └── /meeting/:id — view past meeting
     ↓ REST + WebSocket (proxied via Vite in dev)
FastAPI (port 8000)
  ├── POST /api/auth/register
  ├── POST /api/auth/login
  ├── GET  /api/auth/me
  ├── GET  /api/meetings         (user's meetings list)
  ├── GET  /api/meetings/:id     (transcript + summaries)
  ├── WS   /ws/meeting/:session_id (auth-gated)
  ├── data/meetings.db           (persistent)
  └── tmp/meeting_sessions.db    (Agno agent history, unchanged)
```

**Production (Docker):** Build TanStack Start to static output, serve from FastAPI's `StaticFiles` mount — single container.

## Database Schema

New persistent database at `backend/data/meetings.db` (separate from Agno's `tmp/meeting_sessions.db`):

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meetings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT UNIQUE NOT NULL,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    title            TEXT,
    channel_id       TEXT,
    slack_thread_ts  TEXT,
    status           TEXT DEFAULT 'recording',  -- recording | completed
    duration_seconds INTEGER,
    started_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at         TIMESTAMP
);

CREATE TABLE transcripts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    speaker    INTEGER,
    text       TEXT NOT NULL,
    timestamp  REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE summaries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    type       TEXT NOT NULL,  -- 'chunk' or 'final'
    content    TEXT NOT NULL,
    time_range TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design decisions:**
- Transcripts stored line-by-line (each `is_final=true` Deepgram segment) for speaker-colored display
- Summaries use `type` field to distinguish chunk vs final
- Data written in real-time during meeting (survives crashes)
- Agno's DB stays separate to avoid coupling with internal schema

## Authentication

- **Registration:** username + password + display_name -> bcrypt hash -> store in users -> return JWT
- **Login:** username + password -> verify bcrypt -> return JWT (HS256, 7-day expiry)
- **JWT payload:** `{user_id, username, exp}`
- **Frontend:** JWT in `localStorage`, sent as `Authorization: Bearer <token>` on REST calls
- **WebSocket auth:** JWT as query param `?token=xxx` (WS doesn't support custom headers)
- **New dependencies:** `bcrypt`, `python-jose[cryptography]`

## UI Design

### Layout

- **Desktop (>768px):** Persistent sidebar on left with session list, main content area on right
- **Mobile (<768px):** Hamburger drawer (Shadcn Sidebar with `Sheet` mode), full-width main content
- **Sidebar contents:** "+ New Meeting" button, sessions grouped by date (Today, Yesterday, Last Week, etc.), user info at bottom
- **Dark theme** matching current design (`#0f1117` background)

### Views

1. **Login/Register** — centered card with form fields, minimal design
2. **Dashboard (/)** — active meeting recorder: channel input, start/stop controls, live transcript, live summaries
3. **Meeting History (/meeting/:id)** — meeting header (title, date, duration), tabbed content: Final Summary, Chunk Summaries (time-ranged cards), Full Transcript (speaker-colored)

### Shadcn Components Used

- `Sidebar` — session list navigation
- `Sheet` — mobile drawer overlay
- `Card` — summary cards, meeting cards
- `Button` — actions
- `Input` — form fields
- `Dialog` — confirmations
- `Tabs` — transcript/summaries toggle in history view
- `ScrollArea` — transcript and summary scroll containers
- `Badge` — meeting status indicators

## Frontend Structure

```
frontend/
├── src/
│   ├── routes/
│   │   ├── __root.tsx            (SidebarProvider + auth guard)
│   │   ├── login.tsx
│   │   ├── register.tsx
│   │   ├── index.tsx             (dashboard + active recording)
│   │   └── meeting.$id.tsx       (past meeting detail)
│   ├── components/
│   │   ├── ui/                   (Shadcn components)
│   │   ├── app-sidebar.tsx       (session list sidebar)
│   │   ├── meeting-recorder.tsx  (live recording UI)
│   │   ├── meeting-history.tsx   (past meeting viewer)
│   │   └── transcript-line.tsx   (speaker-colored line)
│   ├── lib/
│   │   ├── api.ts                (REST client with JWT)
│   │   ├── ws-client.ts          (WebSocket client, ported)
│   │   ├── audio-capture.ts      (audio capture, ported)
│   │   └── auth.ts               (token storage, helpers)
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   └── use-meeting.ts
│   ├── router.tsx
│   ├── app.tsx
│   └── styles/app.css
├── public/
│   ├── js/audio-processor.worklet.js
│   └── manifest.json
├── package.json
├── app.config.ts                 (Vite proxy to FastAPI)
└── components.json               (Shadcn config)
```

## Backend Changes

### New files
- `backend/app/database.py` — DB init, connection pool, CRUD for users/meetings/transcripts/summaries
- `backend/app/auth.py` — bcrypt hashing, JWT creation/verification, FastAPI dependency

### Modified files
- `backend/app/main.py` — auth routes, meeting list/detail endpoints, DB startup, WS auth
- `backend/app/session_manager.py` — write transcripts/summaries to persistent DB in real-time, create meeting row on start, update on end, pass user_id through
- `backend/app/config.py` — add `JWT_SECRET`, `DB_PATH` settings
- `backend/pyproject.toml` — add `bcrypt`, `python-jose[cryptography]`

### Unchanged files
- `summarizer.py`, `deepgram_streaming.py`, `slack_client.py`, `models.py`

## Docker / Production

- `compose.yaml`: Add volume mount for `data/` directory (persistence), add frontend build step
- `Dockerfile`: Multi-stage build — stage 1 builds TanStack Start with bun, stage 2 runs FastAPI with built frontend copied in
- FastAPI serves built frontend from `/frontend-dist` as `StaticFiles` mount

## Verification

1. Register + login flow works, JWT persists across page reloads
2. Start meeting, verify live transcript + summaries stream correctly
3. End meeting, verify data persisted in `data/meetings.db`
4. Sidebar shows completed meeting, click to view full history
5. History view shows final summary, chunk summaries with time ranges, full speaker-colored transcript
6. Second user registers, sees only their own meetings
7. Mobile: hamburger drawer works, responsive layout on narrow viewport
8. Docker build works, serves frontend correctly
