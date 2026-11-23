import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # JOBFLOW_ENV_FILE lets tests stay hermetic (point it at os.devnull);
    # the app keeps defaulting to the project .env.
    model_config = SettingsConfigDict(env_file=os.getenv("JOBFLOW_ENV_FILE", ".env"), extra="ignore")

    database_url: str = "sqlite:///./data/jobflow.db"
    host: str = "127.0.0.1"
    port: int = 8000
    # --- LLM (swappable provider, Phase 3+) ---
    llm_provider: str = "openai"          # openai | openrouter | anthropic | ollama | none
    llm_model: str = "gpt-4o-mini"        # for openrouter use a full model id, e.g. openai/gpt-4o-mini
    llm_models: str = ""                  # comma-separated pool (openrouter round-robin/failover)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
