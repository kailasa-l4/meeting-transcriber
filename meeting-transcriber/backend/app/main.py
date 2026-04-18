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
    get_admin_user,
    get_authenticated_user,
    get_current_user,
    get_user_from_ws_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import (
    add_summary,
    add_transcript,
    complete_meeting,
    complete_transcription,
    create_meeting,
    create_transcription,
    create_user,
    dispose_db,
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
    list_users,
    set_user_status,
    soft_delete_user,
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
    try:
        yield
    finally:
        await dispose_db()


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
    status: str
    is_admin: bool


class MeResponse(BaseModel):
    id: int
    username: str
    display_name: str
    status: str
    is_admin: bool
    created_at: str


class UserAdminView(BaseModel):
    id: int
    username: str
    display_name: str
    status: str
    approved_at: str | None
    created_at: str


# -- Auth routes --

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    existing = await get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(req.password)
    user_id = await create_user(req.username, hashed, req.display_name)

    admin_username = get_settings().ADMIN_USERNAME
    is_admin = bool(admin_username) and req.username == admin_username
    if is_admin:
        await set_user_status(user_id, "approved", approved_by=None)
        user_status = "approved"
    else:
        user_status = "pending"

    token = create_token(user_id, req.username)
    return AuthResponse(
        token=token,
        user_id=user_id,
        username=req.username,
        display_name=req.display_name,
        status=user_status,
        is_admin=is_admin,
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user["status"] == "deleted":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    admin_username = get_settings().ADMIN_USERNAME
    is_admin = bool(admin_username) and user["username"] == admin_username
    token = create_token(user["id"], user["username"])
    return AuthResponse(
        token=token,
        user_id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
        status=user["status"],
        is_admin=is_admin,
    )


@app.get("/api/auth/me", response_model=MeResponse)
async def me(user: dict = Depends(get_authenticated_user)):
    admin_username = get_settings().ADMIN_USERNAME
    is_admin = bool(admin_username) and user["username"] == admin_username
    return MeResponse(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
        status=user["status"],
        is_admin=is_admin,
        created_at=user["created_at"].isoformat() if user["created_at"] else "",
    )


# -- Admin routes --

@app.get("/api/admin/users", response_model=list[UserAdminView])
async def admin_list_users(
    status: str | None = None,
    admin: dict = Depends(get_admin_user),
):
    if status and status not in {"pending", "approved", "revoked", "deleted"}:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    users = await list_users(status_filter=status)
    return [
        UserAdminView(
            id=u["id"],
            username=u["username"],
            display_name=u["display_name"],
            status=u["status"],
            approved_at=u["approved_at"].isoformat() if u["approved_at"] else None,
            created_at=u["created_at"].isoformat() if u["created_at"] else "",
        )
        for u in users
    ]


@app.post("/api/admin/users/{user_id}/approve")
async def admin_approve_user(user_id: int, admin: dict = Depends(get_admin_user)):
    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["status"] == "deleted":
        raise HTTPException(status_code=400, detail="Cannot approve a deleted user")
    await set_user_status(user_id, "approved", approved_by=admin["id"])
    return {"ok": True}


@app.post("/api/admin/users/{user_id}/revoke")
async def admin_revoke_user(user_id: int, admin: dict = Depends(get_admin_user)):
    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot revoke yourself")
    if target["status"] == "deleted":
        raise HTTPException(status_code=400, detail="Cannot revoke a deleted user")
    await set_user_status(user_id, "revoked")
    return {"ok": True}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    target = await get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if target["status"] == "deleted":
        raise HTTPException(status_code=400, detail="Already deleted")
    await soft_delete_user(user_id)
    return {"ok": True}


# -- Meeting routes --

@app.get("/api/meetings")
async def list_meetings(current_user: dict = Depends(get_current_user)):
    meetings = await get_meetings_for_user(current_user["id"])
    return meetings


@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: int, current_user: dict = Depends(get_current_user)):
    meeting = await get_meeting_by_id(meeting_id, current_user["id"])
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
    transcription_id = await create_transcription(current_user["id"], file.filename)

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
    return await get_transcriptions_for_user(current_user["id"])


@app.get("/api/transcriptions/{transcription_id}")
async def get_transcription_detail(transcription_id: int, current_user: dict = Depends(get_current_user)):
    t = await get_transcription(transcription_id, current_user["id"])
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
        payload = get_user_from_ws_token(token)
        user = await get_user_by_id(payload["user_id"])
        if not user or user["status"] == "deleted":
            raise ValueError("User not found")
        if user["status"] != "approved":
            await websocket.send_json({"type": "error", "message": "Account not approved"})
            await websocket.close(code=4003)
            return
        user_id = user["id"]
        user_name = user["username"]
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


# -- Static files (SPA) --

from fastapi.responses import FileResponse

frontend_path = Path("/frontend-dist")
if not frontend_path.exists():
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "client"

if frontend_path.exists():
    index_html = frontend_path / "index.html"

    # Mount static asset directories
    assets_dir = frontend_path / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    js_dir = frontend_path / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/manifest.json")
    async def manifest():
        path = frontend_path / "manifest.json"
        if path.exists():
            return FileResponse(path)
        raise HTTPException(status_code=404)

    @app.get("/favicon.ico")
    async def favicon():
        path = frontend_path / "favicon.ico"
        if path.exists():
            return FileResponse(path)
        raise HTTPException(status_code=404)

    # SPA fallback: serve index.html for all non-API, non-WS routes
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404)
        if index_html.exists():
            return FileResponse(index_html)
        raise HTTPException(status_code=404)

    logger.info("Frontend mounted from %s", frontend_path)
else:
    logger.warning("No frontend build found. Serving API only.")
