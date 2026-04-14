import json
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.session_manager import end_meeting, receive_audio, start_meeting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meeting Transcriber")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/session-id")
async def new_session_id():
    return {"session_id": str(uuid.uuid4())[:8]}


@app.websocket("/ws/meeting/{session_id}")
async def meeting_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WebSocket connected: session=%s", session_id)

    session = None
    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                # JSON control message
                data = json.loads(message["text"])
                msg_type = data.get("type", "")

                if msg_type == "start_meeting":
                    session = await start_meeting(
                        session_id=session_id,
                        channel_id=data.get("channel_id"),
                        user_name=data.get("user_name", "Unknown"),
                        client_ws=websocket,
                    )

                elif msg_type == "stop_meeting":
                    await end_meeting(session_id)
                    break

            elif "bytes" in message:
                # Binary audio data
                await receive_audio(session_id, message["bytes"])

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket disconnected: session=%s", session_id)
        if session:
            await end_meeting(session_id)
    except Exception:
        logger.exception("Error in meeting WebSocket: session=%s", session_id)
        if session:
            await end_meeting(session_id)


# Mount frontend static files (must be last to avoid catching API routes)
# Check Docker path first, then local development path
frontend_path = Path("/frontend")
if not frontend_path.exists():
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
