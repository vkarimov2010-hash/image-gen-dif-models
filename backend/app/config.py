from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kie_api_key: str = ""
    kie_base_url: str = "https://api.kie.ai"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/imagegen"

    storage_dir: Path = Path("./storage/images")

    poll_interval_seconds: float = 2.0
    poll_timeout_seconds: float = 300.0

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
