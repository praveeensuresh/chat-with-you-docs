"""App configuration, read from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Claude API (required to run; not needed to import).
    anthropic_api_key: str = ""

    # Qdrant (ADR-0002): local docker in dev, Qdrant Cloud for the demo.
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "documents"

    # Embedding model (ADR-0001): loaded in-process, needs ~0.5-1GB RAM.
    embedding_model: str = "intfloat/e5-base"


settings = Settings()
