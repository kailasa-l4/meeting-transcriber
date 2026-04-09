import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


async def transcribe(audio_bytes: bytes, mimetype: str = "audio/webm") -> str:
    settings = get_settings()

    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": mimetype,
    }
    params = {
        "model": "nova-3",
        "smart_format": "true",
        "punctuate": "true",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            DEEPGRAM_URL,
            headers=headers,
            params=params,
            content=audio_bytes,
        )
        resp.raise_for_status()
        data = resp.json()

    transcript = (
        data["results"]["channels"][0]["alternatives"][0]["transcript"]
    )

    if not transcript:
        logger.warning("Deepgram returned empty transcript")
        return "(empty transcript)"

    logger.info("Transcribed %d characters", len(transcript))
    return transcript
