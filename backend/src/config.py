from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://goldleads:goldleads_dev@localhost:5433/goldleads"
    database_test_url: str = "postgresql+psycopg://goldleads:goldleads_dev@localhost:5433/goldleads_test"
    openrouter_api_key: str = ""
    google_sheet_id: str = ""
    signalhire_api_key: str = ""
    output_dir: str = "../output"
    agno_api_url: str = "http://localhost:8000"
    agno_api_key: str = "dev-key"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
