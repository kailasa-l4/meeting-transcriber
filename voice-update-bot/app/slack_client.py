import logging

import httpx
from slack_sdk import WebClient

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=get_settings().SLACK_BOT_TOKEN)
    return _client


def get_file_info(file_id: str) -> dict:
    resp = _get_client().files_info(file=file_id)
    return resp["file"]


def get_user_info(user_id: str) -> str:
    resp = _get_client().users_info(user=user_id)
    profile = resp["user"]["profile"]
    return profile.get("display_name") or profile.get("real_name") or user_id


async def download_file(url: str) -> bytes:
    token = get_settings().SLACK_BOT_TOKEN
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.content


def post_message(channel_id: str, blocks: list, text: str) -> None:
    _get_client().chat_postMessage(channel=channel_id, blocks=blocks, text=text)
