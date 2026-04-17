from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Project root is two levels up from this file: backend/app/config.py -> backend -> root
ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


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
    DB_PATH: str = "data/meetings.db"
    PORT: int = 8000

    model_config = {"env_file": str(ROOT_ENV)}


@lru_cache
def get_settings() -> Settings:
    return Settings()
