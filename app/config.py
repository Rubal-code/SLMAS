import os
from dataclasses import dataclass


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "SLMAS Agent"
    debug: bool = _bool_env("DEBUG", "false")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/agent.sqlite")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "slmas_memory")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_api_url: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    enable_admin_approval: bool = _bool_env("ENABLE_ADMIN_APPROVAL", "true")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")


settings = Settings()
