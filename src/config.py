"""
Application settings — loaded from environment variables.

Uses pydantic-settings: raises a clear error at startup
if required variables are missing. No hardcoded secrets.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str
    inventory_url: str = "http://localhost:8001"


# Single instance — imported everywhere
settings = Settings()
