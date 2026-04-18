from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_env_file() -> str | None:
    """Look for .env in common locations: project root (dev), /app (docker), CWD."""
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent.parent / ".env",  # dev: project root (backend/app/config.py -> root)
        Path("/app/.env"),                    # docker: if mounted into WORKDIR
        Path.cwd() / ".env",                  # CWD fallback
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


class Settings(BaseSettings):
    SLACK_BOT_TOKEN: str
    DEEPGRAM_API_KEY: str
    OPENROUTER_API_KEY: str
    CHUNK_MODEL: str = "google/gemini-2.0-flash-001"
    FINAL_MODEL: str = "anthropic/claude-sonnet-4"
    MEETING_CHANNEL_ID: str
    SUMMARY_INTERVAL_SECONDS: int = 180
    AUDIO_SAMPLE_RATE: int = 16000
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    DATABASE_URL: str
    ADMIN_USERNAME: str = ""
    PORT: int = 8000

    # env_file is optional; Docker injects env vars directly via compose's env_file directive
    model_config = {"env_file": _find_env_file(), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
