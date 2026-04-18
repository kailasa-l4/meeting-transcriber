import asyncio
import json
import logging
from collections.abc import Callable

import websockets
from websockets.protocol import State as WsState

from app.config import get_settings

logger = logging.getLogger(__name__)

DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramStreaming:
    """WebSocket streaming client for Deepgram Nova-3."""

    def __init__(
        self,
        on_transcript: Callable[[str, bool, int | None, float | None], None],
        sample_rate: int = 16000,
    ):
        self._on_transcript = on_transcript
        self._sample_rate = sample_rate
        self._ws = None
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> None:
        settings = get_settings()

        params = (
            f"?model=nova-3"
            f"&encoding=linear16"
            f"&sample_rate={self._sample_rate}"
            f"&channels=1"
            f"&smart_format=true"
            f"&punctuate=true"
            f"&interim_results=true"
            f"&diarize=true"
        )

        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}

        self._ws = await websockets.connect(
            f"{DEEPGRAM_WS_URL}{params}",
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=10,
        )

        self._receive_task = asyncio.create_task(self._receive_loop())
        logger.info("Deepgram streaming connection established")

    async def send_audio(self, chunk: bytes) -> None:
        if self._ws and self._ws.state == WsState.OPEN:
            await self._ws.send(chunk)

    async def close(self) -> None:
        if self._ws and self._ws.state == WsState.OPEN:
            # Send close message per Deepgram protocol
            await self._ws.send(json.dumps({"type": "CloseStream"}))
            # Wait briefly for final transcripts
            await asyncio.sleep(1)
            await self._ws.close()

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        logger.info("Deepgram streaming connection closed")

    async def _receive_loop(self) -> None:
        try:
            async for message in self._ws:
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "Results":
                    channel = data.get("channel", {})
                    alternatives = channel.get("alternatives", [])
                    if alternatives:
                        alt = alternatives[0]
                        transcript = alt.get("transcript", "")
                        is_final = data.get("is_final", False)
                        if transcript:
                            # Extract speaker + timestamp from word-level data
                            words = alt.get("words", [])
                            speaker = None
                            start_time = None
                            if words:
                                start_time = words[0].get("start")
                                # Dominant speaker = most frequent speaker in this segment
                                speakers = [w.get("speaker") for w in words if w.get("speaker") is not None]
                                if speakers:
                                    speaker = max(set(speakers), key=speakers.count)
                            self._on_transcript(transcript, is_final, speaker, start_time)

                elif msg_type == "Metadata":
                    logger.debug("Deepgram metadata: %s", data)

                elif msg_type == "Error":
                    logger.error("Deepgram error: %s", data)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Deepgram connection closed")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error in Deepgram receive loop")
