from functools import lru_cache

from pydantic_settings import BaseSettings


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

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
