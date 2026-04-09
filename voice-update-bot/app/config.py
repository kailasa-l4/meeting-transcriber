from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    SOURCE_CHANNEL_ID: str
    DEST_CHANNEL_ID: str
    DEEPGRAM_API_KEY: str
    OPENROUTER_API_KEY: str
    LLM_MODEL: str = "anthropic/claude-sonnet-4"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
