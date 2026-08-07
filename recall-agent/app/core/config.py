from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RecallAgent"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://recall_agent:recall_agent@localhost:5432/recall_agent"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
