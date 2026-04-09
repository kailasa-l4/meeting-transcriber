import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.formatter import format_update
from app.slack_client import download_file, get_file_info, get_user_info, post_message
from app.transcriber import transcribe

logger = logging.getLogger(__name__)


def _build_blocks(sender_name: str, formatted_text: str) -> list:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"\U0001f399\ufe0f Voice Update from {sender_name}",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": formatted_text},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{now} | Sent via voice message in #source-channel",
                }
            ],
        },
    ]


async def handle_event(payload: dict) -> None:
    event = payload.get("event", {})
    settings = get_settings()

    channel = event.get("channel")
    if channel != settings.SOURCE_CHANNEL_ID:
        logger.debug("Ignoring message from channel %s", channel)
        return

    if event.get("bot_id") or event.get("subtype") == "bot_message":
        logger.debug("Ignoring bot message")
        return

    files = event.get("files", [])
    audio_files = [f for f in files if f.get("mimetype", "").startswith("audio/")]

    if not audio_files:
        logger.debug("No audio files in message")
        return

    user_id = event.get("user")
    sender_name = get_user_info(user_id) if user_id else "Unknown"

    for file_obj in audio_files:
        file_id = file_obj["id"]
        try:
            file_info = get_file_info(file_id)
            url = file_info.get("url_private_download")
            mimetype = file_info.get("mimetype", "audio/webm")

            if not url:
                logger.error("No download URL for file %s", file_id)
                continue

            logger.info("Downloading audio file %s (%s)", file_id, mimetype)
            audio_bytes = await download_file(url)

            logger.info("Transcribing %d bytes", len(audio_bytes))
            transcript = await transcribe(audio_bytes, mimetype)

            logger.info("Formatting transcript")
            formatted = await format_update(transcript, sender_name)

            blocks = _build_blocks(sender_name, formatted)
            fallback_text = f"Voice update from {sender_name}: {formatted[:200]}"
            post_message(settings.DEST_CHANNEL_ID, blocks, fallback_text)

            logger.info("Posted formatted update for file %s", file_id)

        except Exception:
            logger.exception("Failed to process audio file %s", file_id)
