"""
Centralized configuration for the Lenny Growth Assistant backend.
All runtime knobs (model provider, DB, Ollama host, etc.) live here so the
evaluator can switch behavior via environment variables without touching code.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "Lenny Growth Assistant"
    ENV: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password123@localhost:5432/lenny_assistant"

    # --- LLM provider toggle ---
    # "ollama" (mandatory local demo) or "anthropic" (cloud)
    DEFAULT_LLM_PROVIDER: Literal["ollama", "anthropic"] = "ollama"
    ALLOW_PROVIDER_OVERRIDE_VIA_HEADER: bool = True

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0

    # Anthropic (cloud)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # --- Retrieval ---
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.55
    CHUNK_TARGET_TOKENS: int = 650
    CHUNK_OVERLAP_TOKENS: int = 100

    # --- CORS ---
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
