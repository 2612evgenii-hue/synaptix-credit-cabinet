from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "demo"
    database_url: str = "postgresql+psycopg2://synaptix:synaptix@localhost:5432/synaptix"
    secret_key: str = "change-me-demo-only"
    rules_version: str = "demo-rules-v1"
    risk_model_version: str = "demo-risk-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
