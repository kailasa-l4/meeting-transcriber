# Persistent DB, Multi-User & TanStack UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent SQLite storage, multi-user authentication, and a TanStack Start + Shadcn UI frontend to the meeting transcriber app.

**Architecture:** TanStack Start serves the React frontend with file-based routing and Shadcn components. FastAPI remains the backend handling WebSocket audio streaming, Deepgram, Slack, and Agno summarization. A new persistent SQLite database (`data/meetings.db`) stores users, meetings, transcripts, and summaries. JWT auth gates all endpoints.

**Tech Stack:** TanStack Start, TanStack Router, TanStack Query, Shadcn UI, Tailwind CSS, FastAPI, aiosqlite, bcrypt, python-jose, SQLite

**Spec:** `docs/superpowers/specs/2026-04-14-persistent-db-multiuser-ui-design.md`

**Important context:**
- Use `uv` to run all Python commands (per user preference)
- Use `bun` as the JS runtime/package manager (no node.js available)
- Existing frontend at `frontend/` is vanilla JS — will be replaced entirely
- No test suite exists yet — verify manually per CLAUDE.md
- Agno's `tmp/meeting_sessions.db` stays untouched
- Use Context7 MCP tools for TanStack Start and Shadcn UI docs when implementing

---

## File Map

### New Backend Files
| File | Responsibility |
|------|----------------|
| `backend/app/database.py` | Persistent DB init, table creation, all CRUD functions for users/meetings/transcripts/summaries |
| `backend/app/auth.py` | Password hashing (bcrypt), JWT creation/verification, FastAPI `Depends` for auth |

### Modified Backend Files
| File | Changes |
|------|---------|
| `backend/app/config.py` | Add `JWT_SECRET`, `DB_PATH` settings |
| `backend/pyproject.toml` | Add `bcrypt`, `python-jose[cryptography]` dependencies |
| `backend/app/main.py` | Add auth routes, meeting list/detail endpoints, DB startup lifecycle, WS auth |
| `backend/app/session_manager.py` | Add `user_id`/`meeting_db_id` to MeetingSession, write transcripts/summaries to persistent DB in real-time |
| `backend/Dockerfile` | Multi-stage build: bun frontend build + Python backend |
| `compose.yaml` | Add `data/` volume mount, remove old frontend mount |
| `entrypoint.sh` | Add `mkdir -p /app/data` before server start |

### New Frontend (replaces `frontend/`)
| File | Responsibility |
|------|----------------|
| `frontend/package.json` | TanStack Start + Shadcn + Tailwind dependencies |
| `frontend/app.config.ts` | TanStack Start/Vite config with API proxy |
| `frontend/components.json` | Shadcn UI configuration |
| `frontend/src/app.tsx` | TanStack Start app entry |
| `frontend/src/router.tsx` | Router instance with TanStack Query context |
| `frontend/src/styles/app.css` | Tailwind base + dark theme CSS |
| `frontend/src/routes/__root.tsx` | Root layout: HTML shell, auth guard, SidebarProvider |
| `frontend/src/routes/login.tsx` | Login page |
| `frontend/src/routes/register.tsx` | Register page |
| `frontend/src/routes/index.tsx` | Dashboard: new meeting + active recorder |
| `frontend/src/routes/meeting.$id.tsx` | Past meeting detail view |
| `frontend/src/lib/auth.ts` | Token storage, auth state helpers |
| `frontend/src/lib/api.ts` | REST client with JWT headers |
| `frontend/src/lib/ws-client.ts` | WebSocket client (ported from vanilla JS) |
| `frontend/src/lib/audio-capture.ts` | Audio capture (ported from vanilla JS) |
| `frontend/src/hooks/use-auth.ts` | Auth context provider + hook |
| `frontend/src/hooks/use-meeting.ts` | Active meeting state hook |
| `frontend/src/components/app-sidebar.tsx` | Session list sidebar with date grouping |
| `frontend/src/components/meeting-recorder.tsx` | Live recording UI: controls, transcript, summaries |
| `frontend/src/components/meeting-history.tsx` | Past meeting viewer with tabs |
| `frontend/src/components/transcript-line.tsx` | Speaker-colored transcript line |
| `frontend/public/js/audio-processor.worklet.js` | AudioWorklet processor (copied from current, unchanged) |
| `frontend/public/manifest.json` | PWA manifest (updated) |

---

## Task 1: Backend Config & Dependencies

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add new settings to config.py**

Add `JWT_SECRET` and `DB_PATH` to the Settings class after `AUDIO_SAMPLE_RATE`:

```python
# In backend/app/config.py, add after AUDIO_SAMPLE_RATE: int = 16000
JWT_SECRET: str = "change-me-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_DAYS: int = 7
DB_PATH: str = "data/meetings.db"
```

- [ ] **Step 2: Add new dependencies to pyproject.toml**

Add after `"websockets>=14.0"` in the dependencies list:

```toml
"bcrypt>=4.0.0",
"python-jose[cryptography]>=3.3.0",
```

- [ ] **Step 3: Install dependencies**

Run: `cd backend && uv sync`
Expected: Dependencies install successfully, `uv.lock` updated.

- [ ] **Step 4: Add JWT_SECRET to .env**

Add to `backend/.env`:
```
JWT_SECRET=your-secret-key-change-in-production
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/pyproject.toml backend/uv.lock
git commit -m "feat: add JWT and DB config settings, bcrypt + python-jose deps"
```

---

## Task 2: Database Module

**Files:**
- Create: `backend/app/database.py`

- [ ] **Step 1: Create the data directory**

```bash
mkdir -p backend/data
```

- [ ] **Step 2: Write database.py with schema init and all CRUD functions**

Create `backend/app/database.py`:

```python
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
        """)
        await db.commit()
    logger.info("Database initialized at %s", _db_path)


def _get_db_path() -> str:
    return _db_path


# ── User CRUD ──

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


# ── Meeting CRUD ──

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


# ── Transcript CRUD ──

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


# ── Summary CRUD ──

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
```

- [ ] **Step 3: Verify module imports**

Run: `cd backend && uv run python -c "from app.database import init_db; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/database.py backend/data/
git commit -m "feat: add persistent database module with users, meetings, transcripts, summaries"
```

---

## Task 3: Auth Module

**Files:**
- Create: `backend/app/auth.py`

- [ ] **Step 1: Write auth.py with bcrypt hashing and JWT**

Create `backend/app/auth.py`:

```python
"""Authentication: bcrypt password hashing, JWT creation/verification, FastAPI dependencies."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {"user_id": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency: extract user from JWT in Authorization header."""
    return decode_token(credentials.credentials)


def get_user_from_ws_token(token: str) -> dict:
    """Decode JWT from WebSocket query param. Raises HTTPException on failure."""
    return decode_token(token)
```

- [ ] **Step 2: Verify module imports**

Run: `cd backend && uv run python -c "from app.auth import hash_password, verify_password, create_token; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/auth.py
git commit -m "feat: add auth module with bcrypt hashing and JWT"
```

---

## Task 4: Backend API Endpoints

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Rewrite main.py with auth routes, meeting endpoints, DB lifecycle, and WS auth**

Replace `backend/app/main.py` entirely with:

```python
"""FastAPI application: WebSocket meeting handler, auth routes, meeting history API."""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import (
    create_token,
    decode_token,
    get_current_user,
    get_user_from_ws_token,
    hash_password,
    verify_password,
)
from app.database import (
    add_summary,
    add_transcript,
    complete_meeting,
    create_meeting,
    create_user,
    get_meeting_by_id,
    get_meetings_for_user,
    get_summaries,
    get_transcripts,
    get_user_by_id,
    get_user_by_username,
    init_db,
    update_meeting_slack_thread,
)
from app.session_manager import end_meeting, receive_audio, start_meeting

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


# ── App lifecycle ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Meeting Transcriber", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models for request/response ──

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    display_name: str


# ── Auth routes ──

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    existing = await get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(req.password)
    user_id = await create_user(req.username, hashed, req.display_name)
    token = create_token(user_id, req.username)
    return AuthResponse(token=token, user_id=user_id, username=req.username, display_name=req.display_name)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"], user["username"])
    return AuthResponse(token=token, user_id=user["id"], username=user["username"], display_name=user["display_name"])


@app.get("/api/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    user = await get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Meeting routes ──

@app.get("/api/meetings")
async def list_meetings(current_user: dict = Depends(get_current_user)):
    meetings = await get_meetings_for_user(current_user["user_id"])
    return meetings


@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: int, current_user: dict = Depends(get_current_user)):
    meeting = await get_meeting_by_id(meeting_id, current_user["user_id"])
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    transcripts = await get_transcripts(meeting_id)
    summaries = await get_summaries(meeting_id)
    return {"meeting": meeting, "transcripts": transcripts, "summaries": summaries}


# ── Utility routes ──

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/session-id")
async def new_session_id():
    return {"session_id": uuid.uuid4().hex[:8]}


# ── WebSocket ──

@app.websocket("/ws/meeting/{session_id}")
async def meeting_ws(websocket: WebSocket, session_id: str, token: str = Query(default="")):
    await websocket.accept()

    # Authenticate via JWT query param
    if not token:
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close(code=4001)
        return

    try:
        user_data = get_user_from_ws_token(token)
        user_id = user_data["user_id"]
        user_name = user_data["username"]
    except Exception:
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close(code=4001)
        return

    session = None
    try:
        while True:
            message = await websocket.receive()
            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "start_meeting":
                    channel_id = data.get("channel_id") or None
                    session = await start_meeting(
                        session_id=session_id,
                        channel_id=channel_id,
                        user_name=user_name,
                        user_id=user_id,
                        client_ws=websocket,
                    )

                elif msg_type == "stop_meeting":
                    await end_meeting(session_id)
                    break

            elif "bytes" in message:
                await receive_audio(session_id, message["bytes"])

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)
    except Exception:
        logger.exception("WebSocket error: %s", session_id)
    finally:
        if session:
            try:
                await end_meeting(session_id)
            except Exception:
                logger.exception("Cleanup error: %s", session_id)


# ── Static files ──

frontend_path = Path("/frontend-dist")
if not frontend_path.exists():
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if not frontend_path.exists():
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / ".output" / "public"

if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    logger.warning("No frontend build found. Serving API only.")
```

- [ ] **Step 2: Verify the app starts**

Run: `cd backend && uv run uvicorn app.main:app --reload --reload-exclude .venv --port 8000`
Expected: Server starts, logs "Database initialized at data/meetings.db"

- [ ] **Step 3: Test auth endpoints with curl**

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" -d '{"username":"test","password":"test123","display_name":"Test User"}'
# Expected: {"token":"...","user_id":1,"username":"test","display_name":"Test User"}

# Login
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"test","password":"test123"}'
# Expected: {"token":"...","user_id":1,...}
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: add auth routes, meeting list/detail API, DB lifecycle, WS auth"
```

---

## Task 5: Session Manager — Persistent DB Integration

**Files:**
- Modify: `backend/app/session_manager.py`

- [ ] **Step 1: Add user_id and meeting_db_id to MeetingSession dataclass**

In the `MeetingSession` dataclass, add two new fields after `last_summary_time`:

```python
user_id: int = 0
meeting_db_id: int | None = None
```

- [ ] **Step 2: Add database import at the top of session_manager.py**

Add after the existing `from app.summarizer import ...` line:

```python
from app.database import add_summary, add_transcript, complete_meeting, create_meeting, update_meeting_slack_thread
```

- [ ] **Step 3: Modify start_meeting() signature and add DB writes**

Change the `start_meeting` function signature to accept `user_id`:

```python
async def start_meeting(
    session_id: str,
    channel_id: str | None,
    user_name: str,
    user_id: int,
    client_ws: WebSocket,
) -> MeetingSession:
```

After the session object is created and stored in `_sessions[session_id]`, add:

```python
# Persist meeting to DB
session.user_id = user_id
meeting_db_id = await create_meeting(session_id, user_id, channel_id)
session.meeting_db_id = meeting_db_id
```

After the Slack header is posted (where `slack_thread_ts` is set), add:

```python
if session.slack_thread_ts and session.meeting_db_id:
    await update_meeting_slack_thread(session.meeting_db_id, session.slack_thread_ts)
```

- [ ] **Step 4: Modify _handle_transcript() to write to persistent DB**

After the line that appends to `session.transcript_buffer` (for `is_final=True` only), add:

```python
if session.meeting_db_id:
    await add_transcript(session.meeting_db_id, speaker, text, start_time)
```

- [ ] **Step 5: Modify _summary_loop() to write chunk summaries to persistent DB**

After `session.summaries.append(summary)`, add:

```python
if session.meeting_db_id:
    await add_summary(session.meeting_db_id, "chunk", summary, time_range)
```

- [ ] **Step 6: Modify end_meeting() to store final summary and complete meeting**

After the final summary is generated and posted to Slack, add:

```python
if session.meeting_db_id and final_summary:
    await add_summary(session.meeting_db_id, "final", final_summary)
```

After duration is calculated, add:

```python
if session.meeting_db_id:
    # Use first chunk summary as title, or fallback
    title = session.summaries[0][:80] if session.summaries else f"Meeting {session.session_id}"
    await complete_meeting(session.meeting_db_id, int(duration), title)
```

- [ ] **Step 7: Verify the backend still starts and functions**

Run: `cd backend && uv run uvicorn app.main:app --reload --reload-exclude .venv --port 8000`
Expected: Server starts without import errors.

- [ ] **Step 8: Commit**

```bash
git add backend/app/session_manager.py
git commit -m "feat: write transcripts and summaries to persistent DB in real-time"
```

---

## Task 6: Scaffold TanStack Start Frontend

**Files:**
- Create: entire `frontend/` directory (new TanStack Start project)

**Important:** Use Context7 MCP tools to fetch latest TanStack Start and Shadcn docs during implementation. The docs snippets in the spec should be verified against the latest docs.

- [ ] **Step 1: Rename old frontend directory**

```bash
mv frontend frontend-old
```

- [ ] **Step 2: Create new TanStack Start project with Shadcn**

```bash
bunx shadcn@latest init -t start
# When prompted:
# - Project name: frontend
# - Options: accept defaults for Tailwind, import aliases (@/*)
```

If the CLI doesn't support `bun` natively, fall back to:
```bash
bunx @tanstack/cli@latest create --template start --name frontend
cd frontend
bunx shadcn@latest init
```

- [ ] **Step 3: Install additional dependencies**

```bash
cd frontend
bun add @tanstack/react-query @tanstack/react-query-devtools
```

- [ ] **Step 4: Configure Vite proxy for FastAPI**

In `frontend/app.config.ts`, add the Vite server proxy config:

```typescript
// Add to the vite config section:
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    },
  },
},
```

Verify exact syntax by checking Context7 docs for TanStack Start's `app.config.ts` format — it uses `defineConfig` from `@tanstack/react-start/config` (or Vinxi).

- [ ] **Step 5: Add Shadcn components we'll need**

```bash
cd frontend
bunx shadcn@latest add sidebar sheet card button input tabs scroll-area badge dialog separator
```

- [ ] **Step 6: Set up dark theme in app.css**

Replace the contents of `frontend/src/styles/app.css` (or equivalent global CSS file) with Tailwind base + dark theme variables:

```css
@import "tailwindcss";

:root {
  --background: 222 47% 6%;
  --foreground: 210 40% 98%;
  --card: 222 47% 8%;
  --card-foreground: 210 40% 98%;
  --primary: 239 84% 67%;
  --primary-foreground: 0 0% 100%;
  --secondary: 217 33% 17%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --accent: 217 33% 17%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 84% 60%;
  --destructive-foreground: 0 0% 100%;
  --border: 217 33% 17%;
  --input: 217 33% 17%;
  --ring: 239 84% 67%;
  --sidebar-background: 222 47% 8%;
  --sidebar-foreground: 210 40% 98%;
  --sidebar-primary: 239 84% 67%;
  --sidebar-primary-foreground: 0 0% 100%;
  --sidebar-accent: 217 33% 17%;
  --sidebar-accent-foreground: 210 40% 98%;
  --sidebar-border: 217 33% 17%;
}

body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  font-family: system-ui, -apple-system, sans-serif;
}
```

Adjust to match whatever Shadcn's `init` generates — the key is dark theme with the `#0f1117` style background.

- [ ] **Step 7: Copy AudioWorklet processor (unchanged)**

```bash
mkdir -p frontend/public/js
cp frontend-old/js/audio-processor.worklet.js frontend/public/js/
```

- [ ] **Step 8: Update PWA manifest**

Create `frontend/public/manifest.json`:

```json
{
  "name": "Meeting Transcriber",
  "short_name": "Transcriber",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f1117",
  "theme_color": "#0f1117",
  "description": "Real-time meeting transcription with AI summaries"
}
```

- [ ] **Step 9: Verify dev server starts**

```bash
cd frontend && bun run dev
```
Expected: Vite dev server starts on port 3000 (or similar). Browser shows default TanStack Start page.

- [ ] **Step 10: Commit**

```bash
git add frontend/ -f
git commit -m "feat: scaffold TanStack Start + Shadcn UI frontend with dark theme"
```

---

## Task 7: Frontend Auth Library & Hooks

**Files:**
- Create: `frontend/src/lib/auth.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/use-auth.ts`

- [ ] **Step 1: Write auth.ts — token storage helpers**

Create `frontend/src/lib/auth.ts`:

```typescript
const TOKEN_KEY = "mt_token";
const USER_KEY = "mt_user";

export interface User {
  user_id: number;
  username: string;
  display_name: string;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
```

- [ ] **Step 2: Write api.ts — REST client with JWT headers**

Create `frontend/src/lib/api.ts`:

```typescript
import { getToken, clearAuth } from "./auth";

const BASE_URL = "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }

  return res.json();
}

// Auth
export const authApi = {
  register: (data: { username: string; password: string; display_name: string }) =>
    request<{ token: string; user_id: number; username: string; display_name: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { username: string; password: string }) =>
    request<{ token: string; user_id: number; username: string; display_name: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => request<{ id: number; username: string; display_name: string }>("/api/auth/me"),
};

// Meetings
export interface Meeting {
  id: number;
  session_id: string;
  title: string | null;
  status: string;
  duration_seconds: number | null;
  started_at: string;
  ended_at: string | null;
}

export interface MeetingDetail {
  meeting: Meeting & { channel_id: string; slack_thread_ts: string; user_id: number };
  transcripts: { speaker: number | null; text: string; timestamp: number | null }[];
  summaries: { type: string; content: string; time_range: string | null; created_at: string }[];
}

export const meetingsApi = {
  list: () => request<Meeting[]>("/api/meetings"),
  get: (id: number) => request<MeetingDetail>(`/api/meetings/${id}`),
};
```

- [ ] **Step 3: Write use-auth.ts — React context and hook**

Create `frontend/src/hooks/use-auth.ts`:

```typescript
import { createContext, useContext } from "react";
import type { User } from "@/lib/auth";

export interface AuthContextType {
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function useAuth() {
  return useContext(AuthContext);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/auth.ts frontend/src/lib/api.ts frontend/src/hooks/use-auth.ts
git commit -m "feat: add auth library, API client, and auth hook"
```

---

## Task 8: Frontend WebSocket & Audio Capture (Port from Vanilla JS)

**Files:**
- Create: `frontend/src/lib/ws-client.ts`
- Create: `frontend/src/lib/audio-capture.ts`
- Create: `frontend/src/hooks/use-meeting.ts`

- [ ] **Step 1: Port ws-client.js to TypeScript**

Create `frontend/src/lib/ws-client.ts`. Port the logic from `frontend-old/js/ws-client.js` to TypeScript:

```typescript
import { getToken } from "./auth";

export interface WsCallbacks {
  onTranscript?: (data: { text: string; is_final: boolean; speaker: number; timestamp: number }) => void;
  onSummary?: (data: { summary: string; time_range: string }) => void;
  onStatus?: (data: { state: string; message: string }) => void;
  onError?: (data: { message: string }) => void;
  onClose?: () => void;
  onOpen?: () => void;
}

let ws: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

export function connect(sessionId: string, callbacks: WsCallbacks): void {
  const token = getToken();
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${location.host}/ws/meeting/${sessionId}?token=${token}`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    callbacks.onOpen?.();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "transcript":
          callbacks.onTranscript?.(data);
          break;
        case "summary":
          callbacks.onSummary?.(data);
          break;
        case "status":
          callbacks.onStatus?.(data);
          break;
        case "error":
          callbacks.onError?.(data);
          break;
      }
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = () => {
    callbacks.onClose?.();
  };

  ws.onerror = (err) => {
    console.error("WS error:", err);
  };
}

export function sendStartMeeting(channelId?: string): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "start_meeting", channel_id: channelId || undefined }));
  }
}

export function sendStopMeeting(): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "stop_meeting" }));
  }
}

export function sendAudio(data: ArrayBuffer): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(data);
  }
}

export function disconnect(): void {
  if (ws) {
    ws.close();
    ws = null;
  }
}
```

- [ ] **Step 2: Port audio-capture.js to TypeScript**

Create `frontend/src/lib/audio-capture.ts`. Port from `frontend-old/js/audio-capture.js`:

```typescript
let audioContext: AudioContext | null = null;
let workletNode: AudioWorkletNode | null = null;
let stream: MediaStream | null = null;

export async function startCapture(onChunk: (data: ArrayBuffer) => void): Promise<void> {
  stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  audioContext = new AudioContext({ sampleRate: 16000 });
  await audioContext.audioWorklet.addModule("/js/audio-processor.worklet.js");

  const source = audioContext.createMediaStreamSource(stream);
  workletNode = new AudioWorkletNode(audioContext, "audio-processor");

  workletNode.port.onmessage = (event: MessageEvent) => {
    onChunk(event.data);
  };

  source.connect(workletNode);
  // Don't connect to destination (no feedback)
}

export function stopCapture(): void {
  if (workletNode) {
    workletNode.disconnect();
    workletNode = null;
  }
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
}
```

- [ ] **Step 3: Write use-meeting.ts — active meeting state hook**

Create `frontend/src/hooks/use-meeting.ts`:

```typescript
import { useCallback, useRef, useState } from "react";
import { connect, disconnect, sendAudio, sendStartMeeting, sendStopMeeting } from "@/lib/ws-client";
import { startCapture, stopCapture } from "@/lib/audio-capture";

export interface TranscriptEntry {
  text: string;
  speaker: number | null;
  timestamp: number | null;
  isFinal: boolean;
}

export interface SummaryEntry {
  summary: string;
  timeRange: string;
}

export type MeetingState = "idle" | "starting" | "recording" | "stopping" | "stopped";

export function useMeeting() {
  const [state, setState] = useState<MeetingState>("idle");
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [summaries, setSummaries] = useState<SummaryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionIdRef = useRef<string>("");

  const startMeeting = useCallback(async (channelId?: string) => {
    setError(null);
    setTranscripts([]);
    setSummaries([]);
    setElapsedSeconds(0);
    setState("starting");

    try {
      const res = await fetch("/api/session-id");
      const { session_id } = await res.json();
      sessionIdRef.current = session_id;

      connect(session_id, {
        onTranscript: (data) => {
          setTranscripts((prev) => {
            if (!data.is_final) {
              // Replace last interim entry or add new one
              const withoutInterim = prev.filter((t) => t.isFinal);
              return [...withoutInterim, { text: data.text, speaker: data.speaker, timestamp: data.timestamp, isFinal: false }];
            }
            const withoutInterim = prev.filter((t) => t.isFinal);
            return [...withoutInterim, { text: data.text, speaker: data.speaker, timestamp: data.timestamp, isFinal: true }];
          });
        },
        onSummary: (data) => {
          setSummaries((prev) => [{ summary: data.summary, timeRange: data.time_range }, ...prev]);
        },
        onStatus: (data) => {
          if (data.state === "recording") setState("recording");
          if (data.state === "stopped") {
            setState("stopped");
            stopCapture();
            disconnect();
            if (timerRef.current) clearInterval(timerRef.current);
          }
        },
        onError: (data) => setError(data.message),
        onOpen: () => {
          sendStartMeeting(channelId);
          startCapture(sendAudio);
          timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start meeting");
      setState("idle");
    }
  }, []);

  const stopMeeting = useCallback(() => {
    setState("stopping");
    stopCapture();
    sendStopMeeting();
  }, []);

  return { state, transcripts, summaries, error, elapsedSeconds, startMeeting, stopMeeting };
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/ws-client.ts frontend/src/lib/audio-capture.ts frontend/src/hooks/use-meeting.ts
git commit -m "feat: port WebSocket client, audio capture to TS, add meeting state hook"
```

---

## Task 9: Root Layout & Auth Provider

**Files:**
- Modify: `frontend/src/routes/__root.tsx`
- Modify: `frontend/src/router.tsx`

- [ ] **Step 1: Set up router.tsx with TanStack Query context**

Update `frontend/src/router.tsx` to include QueryClient in the router context:

```typescript
import { createRouter } from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";
import { routeTree } from "./routeTree.gen";

export function getRouter() {
  const queryClient = new QueryClient();

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
  });

  return router;
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>;
  }
}
```

- [ ] **Step 2: Write __root.tsx with auth provider, sidebar layout, and auth guard**

Update `frontend/src/routes/__root.tsx`:

```tsx
import { useState, useCallback, useEffect } from "react";
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
  useNavigate,
  useLocation,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { AuthContext } from "@/hooks/use-auth";
import { getStoredUser, setAuth, clearAuth as clearStoredAuth, isAuthenticated } from "@/lib/auth";
import type { User } from "@/lib/auth";
import appCss from "@/styles/app.css?url";

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1.0, user-scalable=no" },
      { name: "theme-color", content: "#0f1117" },
      { name: "apple-mobile-web-app-capable", content: "yes" },
      { name: "apple-mobile-web-app-status-bar-style", content: "black-translucent" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "manifest", href: "/manifest.json" },
    ],
  }),
  component: RootComponent,
});

function RootComponent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<User | null>(getStoredUser());

  const login = useCallback((token: string, userData: User) => {
    setAuth(token, userData);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    clearStoredAuth();
    setUser(null);
    navigate({ to: "/login" });
  }, [navigate]);

  const authed = isAuthenticated() && user !== null;

  // Auth guard: redirect unauthenticated users to /login
  useEffect(() => {
    const publicPaths = ["/login", "/register"];
    if (!authed && !publicPaths.includes(location.pathname)) {
      navigate({ to: "/login" });
    }
  }, [authed, location.pathname, navigate]);

  const isPublicPage = ["/login", "/register"].includes(location.pathname);

  return (
    <RootDocument>
      <QueryClientProvider client={Route.useRouteContext().queryClient}>
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: authed }}>
          {authed && !isPublicPage ? (
            <SidebarProvider>
              <AppSidebar />
              <main className="flex-1 flex flex-col min-h-dvh overflow-hidden">
                <Outlet />
              </main>
            </SidebarProvider>
          ) : (
            <Outlet />
          )}
        </AuthContext.Provider>
      </QueryClientProvider>
    </RootDocument>
  );
}

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-dvh bg-background text-foreground">
        {children}
        <Scripts />
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router.tsx frontend/src/routes/__root.tsx
git commit -m "feat: add root layout with auth provider, sidebar, and auth guard"
```

---

## Task 10: Login & Register Pages

**Files:**
- Create: `frontend/src/routes/login.tsx`
- Create: `frontend/src/routes/register.tsx`

- [ ] **Step 1: Write login.tsx**

Create `frontend/src/routes/login.tsx`:

```tsx
import { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { authApi } from "@/lib/api";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login({ username, password });
      login(res.token, { user_id: res.user_id, username: res.username, display_name: res.display_name });
      navigate({ to: "/" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Meeting Transcriber</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Signing in..." : "Sign In"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              No account?{" "}
              <Link to="/register" className="text-primary underline">
                Register
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Write register.tsx**

Create `frontend/src/routes/register.tsx`:

```tsx
import { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { authApi } from "@/lib/api";

export const Route = createFileRoute("/register")({
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.register({ username, password, display_name: displayName });
      login(res.token, { user_id: res.user_id, username: res.username, display_name: res.display_name });
      navigate({ to: "/" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Join Meeting Transcriber</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Input
              placeholder="Display Name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
            <Input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Creating account..." : "Create Account"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              Have an account?{" "}
              <Link to="/login" className="text-primary underline">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: Verify dev server shows login page**

Run both servers:
- Backend: `cd backend && uv run uvicorn app.main:app --reload --reload-exclude .venv --port 8000`
- Frontend: `cd frontend && bun run dev`

Navigate to `http://localhost:3000/login`. Expected: dark-themed login card renders.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/login.tsx frontend/src/routes/register.tsx
git commit -m "feat: add login and register pages"
```

---

## Task 11: App Sidebar Component

**Files:**
- Create: `frontend/src/components/app-sidebar.tsx`

- [ ] **Step 1: Write app-sidebar.tsx with session list grouped by date**

Create `frontend/src/components/app-sidebar.tsx`:

```tsx
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { meetingsApi, type Meeting } from "@/lib/api";

function groupByDate(meetings: Meeting[]): Record<string, Meeting[]> {
  const groups: Record<string, Meeting[]> = {};
  const now = new Date();
  const today = now.toDateString();
  const yesterday = new Date(now.getTime() - 86400000).toDateString();

  for (const m of meetings) {
    const d = new Date(m.started_at).toDateString();
    let label: string;
    if (d === today) label = "Today";
    else if (d === yesterday) label = "Yesterday";
    else label = new Date(m.started_at).toLocaleDateString("en-US", { month: "short", day: "numeric" });

    if (!groups[label]) groups[label] = [];
    groups[label].push(m);
  }
  return groups;
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  return `${m}m`;
}

export function AppSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: meetings = [] } = useQuery({
    queryKey: ["meetings"],
    queryFn: meetingsApi.list,
    refetchInterval: 10000,
  });

  const grouped = groupByDate(meetings);

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-lg">Meetings</span>
          <SidebarTrigger />
        </div>
        <Button
          className="w-full mt-2"
          onClick={() => navigate({ to: "/" })}
        >
          + New Meeting
        </Button>
      </SidebarHeader>

      <SidebarContent>
        {Object.entries(grouped).map(([label, items]) => (
          <SidebarGroup key={label}>
            <SidebarGroupLabel>{label}</SidebarGroupLabel>
            <SidebarMenu>
              {items.map((m) => (
                <SidebarMenuItem key={m.id}>
                  <SidebarMenuButton asChild>
                    <Link to="/meeting/$id" params={{ id: String(m.id) }}>
                      <span className="truncate flex-1">
                        {m.title || `Meeting ${m.session_id}`}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {m.status === "recording" ? (
                          <Badge variant="destructive" className="text-xs">Live</Badge>
                        ) : (
                          formatDuration(m.duration_seconds)
                        )}
                      </span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-border">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground truncate">{user?.display_name}</span>
          <Button variant="ghost" size="sm" onClick={logout}>
            Sign out
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/app-sidebar.tsx
git commit -m "feat: add app sidebar with date-grouped meeting list"
```

---

## Task 12: Dashboard & Meeting Recorder

**Files:**
- Create: `frontend/src/components/transcript-line.tsx`
- Create: `frontend/src/components/meeting-recorder.tsx`
- Create: `frontend/src/routes/index.tsx`

- [ ] **Step 1: Write transcript-line.tsx — speaker-colored line**

Create `frontend/src/components/transcript-line.tsx`:

```tsx
const SPEAKER_COLORS = [
  "text-blue-400",
  "text-green-400",
  "text-yellow-400",
  "text-purple-400",
  "text-pink-400",
  "text-cyan-400",
];

interface TranscriptLineProps {
  speaker: number | null;
  text: string;
  isFinal: boolean;
}

export function TranscriptLine({ speaker, text, isFinal }: TranscriptLineProps) {
  const color = speaker !== null ? SPEAKER_COLORS[speaker % SPEAKER_COLORS.length] : "text-muted-foreground";

  return (
    <div className={`text-sm py-0.5 ${!isFinal ? "italic opacity-60" : ""}`}>
      {speaker !== null && (
        <span className={`font-medium ${color} mr-1`}>S{speaker}:</span>
      )}
      <span>{text}</span>
    </div>
  );
}
```

- [ ] **Step 2: Write meeting-recorder.tsx — full recording UI**

Create `frontend/src/components/meeting-recorder.tsx`:

```tsx
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import { useMeeting } from "@/hooks/use-meeting";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function MeetingRecorder() {
  const [channelId, setChannelId] = useState("");
  const { state, transcripts, summaries, error, elapsedSeconds, startMeeting, stopMeeting } = useMeeting();
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  const isRecording = state === "recording" || state === "starting";
  const isStopping = state === "stopping";
  const isStopped = state === "stopped";

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-border">
        <SidebarTrigger className="md:hidden" />
        <h1 className="font-semibold text-lg flex-1">Meeting Transcriber</h1>
        {isRecording && (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-sm text-muted-foreground font-mono">{formatTime(elapsedSeconds)}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="p-4 space-y-3 border-b border-border">
        <Input
          placeholder="Slack Channel ID (optional)"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          disabled={isRecording || isStopping}
        />
        <div className="flex gap-2">
          {!isRecording && !isStopping && !isStopped && (
            <Button onClick={() => startMeeting(channelId || undefined)} className="flex-1">
              Start Meeting
            </Button>
          )}
          {isRecording && (
            <Button variant="destructive" onClick={stopMeeting} className="flex-1">
              Stop Meeting
            </Button>
          )}
          {isStopping && (
            <Button disabled className="flex-1">
              Generating summary...
            </Button>
          )}
          {isStopped && (
            <Button onClick={() => window.location.reload()} className="flex-1">
              New Meeting
            </Button>
          )}
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col gap-4 p-4">
        {/* Transcript */}
        <div className="flex-1 min-h-0">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Live Transcript</h3>
          <ScrollArea className="h-full max-h-[300px] rounded-md border border-border p-3">
            {transcripts.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {isRecording ? "Listening..." : "Start a meeting to begin transcription"}
              </p>
            )}
            {transcripts.map((t, i) => (
              <TranscriptLine key={i} speaker={t.speaker} text={t.text} isFinal={t.isFinal} />
            ))}
            <div ref={transcriptEndRef} />
          </ScrollArea>
        </div>

        {/* Summaries */}
        <div className="flex-1 min-h-0">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Summaries</h3>
          <ScrollArea className="h-full max-h-[300px]">
            {summaries.length === 0 && (
              <p className="text-sm text-muted-foreground">Summaries will appear every 3 minutes</p>
            )}
            <div className="space-y-2">
              {summaries.map((s, i) => (
                <Card key={i}>
                  <CardHeader className="py-2 px-3">
                    <CardTitle className="text-xs font-medium">
                      <Badge variant="secondary">{s.timeRange}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 pt-0">
                    <p className="text-sm whitespace-pre-wrap">{s.summary}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write index.tsx route**

Create `frontend/src/routes/index.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { MeetingRecorder } from "@/components/meeting-recorder";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  return <MeetingRecorder />;
}
```

- [ ] **Step 4: Verify the dashboard renders**

With both servers running, navigate to `http://localhost:3000/`. After logging in, should see the dark-themed dashboard with sidebar, controls, transcript area, and summaries area.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/transcript-line.tsx frontend/src/components/meeting-recorder.tsx frontend/src/routes/index.tsx
git commit -m "feat: add dashboard with meeting recorder, live transcript, and summaries"
```

---

## Task 13: Meeting History View

**Files:**
- Create: `frontend/src/components/meeting-history.tsx`
- Create: `frontend/src/routes/meeting.$id.tsx`

- [ ] **Step 1: Write meeting-history.tsx**

Create `frontend/src/components/meeting-history.tsx`:

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import type { MeetingDetail } from "@/lib/api";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "Unknown duration";
  const m = Math.floor(seconds / 60);
  return `${m} min`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

interface MeetingHistoryProps {
  data: MeetingDetail;
}

export function MeetingHistory({ data }: MeetingHistoryProps) {
  const { meeting, transcripts, summaries } = data;
  const chunkSummaries = summaries.filter((s) => s.type === "chunk");
  const finalSummary = summaries.find((s) => s.type === "final");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <SidebarTrigger className="md:hidden" />
          <div className="flex-1">
            <h1 className="font-semibold text-lg">{meeting.title || `Meeting ${meeting.session_id}`}</h1>
            <p className="text-sm text-muted-foreground">
              {formatDate(meeting.started_at)} &middot; {formatDuration(meeting.duration_seconds)}
            </p>
          </div>
          <Badge variant={meeting.status === "completed" ? "secondary" : "destructive"}>
            {meeting.status}
          </Badge>
        </div>
      </div>

      {/* Tabbed content */}
      <Tabs defaultValue="summary" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-4 mt-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="flex-1 overflow-auto p-4 space-y-4">
          {finalSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Final Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">{finalSummary.content}</div>
              </CardContent>
            </Card>
          )}

          {chunkSummaries.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">Interim Summaries</h3>
              {chunkSummaries.map((s, i) => (
                <Card key={i}>
                  <CardHeader className="py-2 px-3">
                    <CardTitle className="text-xs">
                      <Badge variant="outline">{s.time_range || `Chunk ${i + 1}`}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 pt-0">
                    <p className="text-sm whitespace-pre-wrap">{s.content}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!finalSummary && chunkSummaries.length === 0 && (
            <p className="text-muted-foreground text-sm">No summaries available for this meeting.</p>
          )}
        </TabsContent>

        <TabsContent value="transcript" className="flex-1 overflow-hidden p-4">
          <ScrollArea className="h-full">
            {transcripts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No transcript available.</p>
            ) : (
              transcripts.map((t, i) => (
                <TranscriptLine key={i} speaker={t.speaker} text={t.text} isFinal={true} />
              ))
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

- [ ] **Step 2: Write meeting.$id.tsx route with TanStack Query loader**

Create `frontend/src/routes/meeting.$id.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { meetingsApi } from "@/lib/api";
import { MeetingHistory } from "@/components/meeting-history";

export const Route = createFileRoute("/meeting/$id")({
  component: MeetingPage,
});

function MeetingPage() {
  const { id } = Route.useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["meeting", id],
    queryFn: () => meetingsApi.get(Number(id)),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading meeting...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">Failed to load meeting</p>
      </div>
    );
  }

  return <MeetingHistory data={data} />;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/meeting-history.tsx frontend/src/routes/meeting.\$id.tsx
git commit -m "feat: add meeting history view with summary and transcript tabs"
```

---

## Task 14: Docker Multi-Stage Build & Compose

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `compose.yaml`
- Modify: `entrypoint.sh`

- [ ] **Step 1: Rewrite Dockerfile as multi-stage build**

Replace `backend/Dockerfile`:

```dockerfile
# Stage 1: Build frontend with Bun
FROM oven/bun:latest AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY frontend/ .
RUN bun run build

# Stage 2: Python backend
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install cloudflared
RUN apt-get update && apt-get install -y curl && \
    curl -L --output /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && \
    chmod +x /usr/local/bin/cloudflared && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen 2>/dev/null || uv sync

# Copy backend code
COPY backend/app ./app

# Copy built frontend
COPY --from=frontend-build /app/dist /frontend-dist

# Ensure data directory exists
RUN mkdir -p /app/data

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
```

Note: The exact build output path (`/app/dist`, `/app/.output/public`, etc.) depends on TanStack Start's build config. Verify with `bun run build` output and adjust the `COPY --from` path accordingly.

- [ ] **Step 2: Update compose.yaml with data volume**

Replace `compose.yaml`:

```yaml
services:
  transcriber:
    build:
      context: .
      dockerfile: backend/Dockerfile
    env_file: backend/.env
    volumes:
      - ./data:/app/data
    expose:
      - "8000"
    ports:
      - "8001:8000"
    restart: unless-stopped
```

- [ ] **Step 3: Update entrypoint.sh to ensure data directory**

Add `mkdir -p /app/data` before the uvicorn line in `entrypoint.sh`.

- [ ] **Step 4: Add data/ to .gitignore**

Create or update `.gitignore` to include:
```
data/*.db
frontend-old/
```

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile compose.yaml entrypoint.sh .gitignore
git commit -m "feat: multi-stage Docker build with bun frontend, persistent data volume"
```

---

## Task 15: Integration Verification

- [ ] **Step 1: Start both servers locally**

Terminal 1: `cd backend && uv run uvicorn app.main:app --reload --reload-exclude .venv --port 8000`
Terminal 2: `cd frontend && bun run dev`

- [ ] **Step 2: Test full registration and login flow**

1. Navigate to `http://localhost:3000/login`
2. Click "Register" link
3. Fill form: display name, username, password
4. Submit — should redirect to dashboard

- [ ] **Step 3: Test meeting recording**

1. On dashboard, optionally enter Slack channel ID
2. Click "Start Meeting"
3. Speak into microphone — verify live transcript appears with speaker colors
4. Wait 3+ minutes — verify chunk summary card appears
5. Click "Stop Meeting" — verify final summary generation
6. Check sidebar — meeting should appear under "Today"

- [ ] **Step 4: Test meeting history**

1. Click the completed meeting in the sidebar
2. Verify Summary tab shows final summary and chunk summaries
3. Switch to Transcript tab — verify speaker-colored transcript lines
4. Check the duration and title display

- [ ] **Step 5: Test multi-user isolation**

1. Sign out
2. Register a second user
3. Verify they see an empty session list (no meetings from user 1)

- [ ] **Step 6: Test mobile layout**

1. Open browser DevTools, toggle device toolbar (responsive mode)
2. Set to iPhone width (~375px)
3. Verify sidebar is hidden, hamburger icon shows
4. Tap hamburger — sidebar drawer slides in
5. Navigate between views — verify layout is usable

- [ ] **Step 7: Clean up old frontend**

Once everything works:
```bash
rm -rf frontend-old
git add -A
git commit -m "chore: remove old vanilla JS frontend"
```

- [ ] **Step 8: Test Docker build (optional)**

```bash
docker compose up --build
```
Navigate to `http://localhost:8001` — verify full app works from the Docker build.
