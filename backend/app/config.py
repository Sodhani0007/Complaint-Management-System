"""
Centralized application configuration.

Why this exists: every mutable, environment-specific value (DB URL, API keys,
CORS origins, upload limits) lives in exactly one place. Nothing in services/,
ai/, or api/ should ever read os.environ directly — they import `settings`
from here. This is what makes it possible to point the whole app at a
different DB or API key just by changing .env, with zero code changes.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App ---
    APP_NAME: str = "Complaint Management System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/complaints_db"

    # --- Groq / LLM ---
    GROQ_API_KEY: str = ""
    GROQ_EXTRACTION_MODEL: str = "gemma2-9b-it"
    GROQ_REASONING_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: int = 30

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".txt", ".eml")
    UPLOAD_STORAGE_DIR: str = "./uploaded_documents"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """
    Cached so Settings() — which reads .env and validates types — only runs
    once per process, not on every request that depends on it.
    """
    return Settings()


settings = get_settings()
