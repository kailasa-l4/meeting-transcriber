"""Transcribe audio/video files using Deepgram's pre-recorded API."""

import json
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


async def transcribe_file(file_bytes: bytes, content_type: str) -> dict:
    """Send audio/video file to Deepgram pre-recorded API.

    Returns dict with keys: transcript, segments, duration_seconds
    """
    settings = get_settings()

    params = {
        "model": "nova-3",
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "true",
    }

    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": content_type,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            DEEPGRAM_URL,
            params=params,
            headers=headers,
            content=file_bytes,
        )
        response.raise_for_status()
        data = response.json()

    # Parse the response
    result = data.get("results", {})
    channels = result.get("channels", [])

    if not channels:
        return {"transcript": "", "segments": "[]", "duration_seconds": 0}

    alternatives = channels[0].get("alternatives", [])
    if not alternatives:
        return {"transcript": "", "segments": "[]", "duration_seconds": 0}

    best = alternatives[0]
    transcript = best.get("transcript", "")

    # Extract speaker-diarized segments from paragraphs or words
    segments = []
    paragraphs = best.get("paragraphs", {}).get("paragraphs", [])
    if paragraphs:
        for para in paragraphs:
            for sentence in para.get("sentences", []):
                segments.append({
                    "speaker": para.get("speaker", 0),
                    "text": sentence.get("text", ""),
                    "start": sentence.get("start", 0),
                    "end": sentence.get("end", 0),
                })
    else:
        # Fallback: use words to build segments
        words = best.get("words", [])
        current_speaker = None
        current_text = []
        current_start = 0
        for w in words:
            speaker = w.get("speaker", 0)
            if speaker != current_speaker:
                if current_text:
                    segments.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_text),
                        "start": current_start,
                        "end": w.get("start", 0),
                    })
                current_speaker = speaker
                current_text = [w.get("punctuated_word", w.get("word", ""))]
                current_start = w.get("start", 0)
            else:
                current_text.append(w.get("punctuated_word", w.get("word", "")))
        if current_text:
            segments.append({
                "speaker": current_speaker,
                "text": " ".join(current_text),
                "start": current_start,
                "end": words[-1].get("end", 0) if words else 0,
            })

    # Duration from metadata
    duration = data.get("metadata", {}).get("duration", 0)

    return {
        "transcript": transcript,
        "segments": json.dumps(segments),
        "duration_seconds": int(duration) if duration else None,
    }
