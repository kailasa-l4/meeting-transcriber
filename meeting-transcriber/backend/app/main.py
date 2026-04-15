"""FastAPI application: WebSocket meeting handler, auth routes, meeting history API."""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
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
    complete_transcription,
    create_meeting,
    create_transcription,
    create_user,
    fail_transcription,
    get_meeting_by_id,
    get_meetings_for_user,
    get_summaries,
    get_transcription,
    get_transcriptions_for_user,
    get_transcripts,
    get_user_by_id,
    get_user_by_username,
    init_db,
    update_meeting_slack_thread,
)
from app.session_manager import end_meeting, receive_audio, start_meeting
from app.transcribe_file import transcribe_file

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


# -- App lifecycle --

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


# -- Pydantic models for request/response --

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


# -- Auth routes --

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


# -- Meeting routes --

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


# -- Utility routes --

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/session-id")
async def new_session_id():
    return {"session_id": uuid.uuid4().hex[:8]}


# -- Transcription routes --

@app.post("/api/transcriptions/upload")
async def upload_transcription(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Create DB record
    transcription_id = await create_transcription(current_user["user_id"], file.filename)

    try:
        file_bytes = await file.read()
        content_type = file.content_type or "audio/wav"

        result = await transcribe_file(file_bytes, content_type)

        await complete_transcription(
            transcription_id,
            result["transcript"],
            result["segments"],
            result["duration_seconds"],
        )

        return {
            "id": transcription_id,
            "status": "completed",
            "transcript": result["transcript"],
            "segments": result["segments"],
            "duration_seconds": result["duration_seconds"],
        }
    except Exception as e:
        logger.exception("Transcription failed for file: %s", file.filename)
        await fail_transcription(transcription_id, str(e))
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.get("/api/transcriptions")
async def list_transcriptions(current_user: dict = Depends(get_current_user)):
    return await get_transcriptions_for_user(current_user["user_id"])


@app.get("/api/transcriptions/{transcription_id}")
async def get_transcription_detail(transcription_id: int, current_user: dict = Depends(get_current_user)):
    t = await get_transcription(transcription_id, current_user["user_id"])
    if not t:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return t


# -- WebSocket --

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


# -- Static files --

frontend_path = Path("/frontend-dist")
if not frontend_path.exists():
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if not frontend_path.exists():
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / ".output" / "public"

if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    logger.warning("No frontend build found. Serving API only.")
