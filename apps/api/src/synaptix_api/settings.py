from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "demo"
    database_url: str = "postgresql+psycopg2://synaptix:synaptix@localhost:5432/synaptix"
    secret_key: str = "change-me-demo-only"
    rules_version: str = "demo-rules-v1"
    risk_model_version: str = "demo-risk-v1"
    # Open-weight LLM explain (optional). Default template — credit path never depends on LLM.
    # llm_backend: template | ollama  (local Ollama-compatible runtime only)
    llm_backend: str = "template"
    llm_base_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen3:4b"  # open-weight candidate; see ai/model-manifest.json
    llm_timeout_seconds: float = 8.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
