import asyncio
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT_TEMPLATE = (
    "You are formatting a voice update from a team member named {sender_name}. "
    "Extract and format: "
    "1) A one-line summary "
    "2) Key updates/status points "
    "3) Action items (if any) "
    "4) Blockers (if any). "
    "Keep it concise. Use plain text, no markdown headers. "
    "If a section has nothing, omit it."
)


async def format_update(transcript: str, sender_name: str) -> str:
    settings = get_settings()

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(sender_name=sender_name)

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    formatted = data["choices"][0]["message"]["content"]
    logger.info("Formatted update: %d characters", len(formatted))
    return formatted
