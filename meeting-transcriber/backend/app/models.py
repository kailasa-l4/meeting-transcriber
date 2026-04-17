from enum import Enum

from pydantic import BaseModel


class SessionState(str, Enum):
    STARTING = "starting"
    RECORDING = "recording"
    STOPPING = "stopping"
    STOPPED = "stopped"


# Client -> Server (JSON control messages over WebSocket)

class StartMeeting(BaseModel):
    type: str = "start_meeting"
    channel_id: str | None = None  # Override default channel
    user_name: str = "Unknown"


class StopMeeting(BaseModel):
    type: str = "stop_meeting"


# Server -> Client (JSON messages over WebSocket)

class TranscriptUpdate(BaseModel):
    type: str = "transcript"
    text: str
    is_final: bool
    speaker: int | None = None
    timestamp: float | None = None


class SummaryPosted(BaseModel):
    type: str = "summary"
    summary: str
    time_range: str


class StatusUpdate(BaseModel):
    type: str = "status"
    state: SessionState
    message: str = ""


class ErrorMessage(BaseModel):
    type: str = "error"
    message: str
