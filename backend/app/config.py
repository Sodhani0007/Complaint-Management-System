"""
Centralized application configuration.

Why this exists: every mutable, environment-specific value (DB URL, API keys,
CORS origins, upload limits) lives in exactly one place. Nothing in services/,
ai/, or api/ should ever read os.environ directly — they import `settings`
from here. This is what makes it possible to point the whole app at a
different DB or API key just by changing .env, with zero code changes.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App ---
    APP_NAME: str = "Complaint Management System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DEMO_MODE: bool = False
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    SESSION_TTL_MINUTES: int = Field(default=60, ge=5, le=1440)
    AI_REQUESTS_PER_DAY: int = Field(default=30, ge=0)
    COMPLAINTS_PER_DAY: int = Field(default=100, ge=0)
    MAX_TEXT_LENGTH: int = Field(default=20000, ge=1, le=100000)

    @model_validator(mode="after")
    def validate_deployment(self):
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if bool(self.ADMIN_EMAIL) != bool(self.ADMIN_PASSWORD):
            raise ValueError("Set both ADMIN_EMAIL and ADMIN_PASSWORD")
        if self.ADMIN_PASSWORD and len(self.ADMIN_PASSWORD) < 16:
            raise ValueError("ADMIN_PASSWORD must contain at least 16 characters")
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/complaints_db"

    # --- Groq / LLM ---
    # NOTE: the assignment's originally-specified models (gemma2-9b-it,
    # llama-3.3-70b-versatile) have since been deprecated/scheduled for
    # shutdown by Groq (see https://console.groq.com/docs/deprecations,
    # checked 2026-08-08). Using their currently-recommended, non-deprecated
    # replacements instead. If Groq's lineup changes again, check that page
    # and update these two defaults (or override via .env — nothing else in
    # the codebase needs to change, since llm_client.py takes the model name
    # as a parameter rather than hardcoding it).
    GROQ_API_KEY: str = ""
    GROQ_EXTRACTION_MODEL: str = "openai/gpt-oss-20b"
    GROQ_REASONING_MODEL: str = "openai/gpt-oss-120b"
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
