"""App settings. Every setting is read from the environment / the `.env` file in one place.

A typo in a variable name fails loudly at start-up instead of randomly later.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root = backend/app/core/config.py -> three levels up
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://tedu:tedu@localhost:5432/tedu"
    jwt_secret: str = "change-me"
    cors_origins: str = "http://localhost:5173"  # comma separated list
    openai_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """One cached Settings object, imported everywhere."""
    return Settings()
