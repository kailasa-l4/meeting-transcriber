import logging

from slack_sdk import WebClient

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=get_settings().SLACK_BOT_TOKEN)
    return _client


def post_meeting_header(channel: str, user_name: str) -> str:
    """Post initial meeting header message. Returns thread_ts."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Meeting Transcription In Progress",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Started by *{user_name}*\nLive transcription and periodic summaries will appear in this thread.",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Status: :red_circle: Recording...",
                }
            ],
        },
    ]

    resp = _get_client().chat_postMessage(
        channel=channel,
        blocks=blocks,
        text=f"Meeting transcription started by {user_name}",
    )
    thread_ts = resp["ts"]
    logger.info("Posted meeting header, thread_ts=%s", thread_ts)
    return thread_ts


def post_threaded_summary(
    channel: str, thread_ts: str, summary: str, time_range: str
) -> None:
    """Post a periodic summary as a threaded reply."""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary ({time_range})*\n\n{summary}",
            },
        },
    ]

    _get_client().chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        blocks=blocks,
        text=f"Summary ({time_range}): {summary[:200]}",
    )
    logger.info("Posted threaded summary for %s", time_range)


def _split_text_blocks(text: str, limit: int = 2900) -> list[str]:
    """Split text into chunks that fit within Slack's 3000-char block limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # Split at last newline before limit
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def post_final_summary(channel: str, thread_ts: str, summary: str) -> None:
    """Post the final comprehensive summary in the thread."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Meeting Summary (Final)",
            },
        },
    ]

    for chunk in _split_text_blocks(summary):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": chunk,
            },
        })

    _get_client().chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        blocks=blocks,
        text=f"Final meeting summary: {summary[:200]}",
    )
    logger.info("Posted final summary")


def upload_audio_file(
    channel: str, thread_ts: str, file_path: str, title: str
) -> None:
    """Upload meeting audio recording to the Slack thread."""
    _get_client().files_upload_v2(
        channel=channel,
        thread_ts=thread_ts,
        file=file_path,
        title=title,
        initial_comment="Meeting audio recording",
    )
    logger.info("Uploaded audio file: %s", title)


def update_meeting_header(channel: str, ts: str, duration_str: str) -> None:
    """Update the original header message to show meeting is complete."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Meeting Transcription Complete",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Duration: {duration_str} | :white_check_mark: Complete — see thread for summaries",
                }
            ],
        },
    ]

    _get_client().chat_update(
        channel=channel,
        ts=ts,
        blocks=blocks,
        text=f"Meeting transcription complete ({duration_str})",
    )
    logger.info("Updated meeting header to complete")
