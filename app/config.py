import os
from dataclasses import dataclass, field


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _list_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default).strip()

    if not raw_value:
        return []

    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


@dataclass(frozen=True)
class Settings:
    app_name: str = "SLMAS Agent"
    app_version: str = "0.3.0"

    environment: str = os.getenv(
        "APP_ENV",
        "development",
    )

    debug: bool = _bool_env(
        "DEBUG",
        "false",
    )

    port: int = int(
        os.getenv("PORT", "8000")
    )

    workers: int = int(
        os.getenv("WORKERS", "2")
    )

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/agent.sqlite",
    )

    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    qdrant_url: str = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333",
    )

    qdrant_collection: str = os.getenv(
        "QDRANT_COLLECTION",
        "slmas_memory",
    )

    qdrant_api_key: str = os.getenv(
        "QDRANT_API_KEY",
        "",
    )

    groq_api_key: str = os.getenv(
        "GROQ_API_KEY",
        "",
    )

    groq_api_url: str = os.getenv(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1",
    )

    groq_model: str = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    enable_admin_approval: bool = _bool_env(
        "ENABLE_ADMIN_APPROVAL",
        "true",
    )

    secret_key: str = os.getenv(
        "SECRET_KEY",
        "change-me-in-production",
    )

    sentry_dsn: str = os.getenv(
        "SENTRY_DSN",
        "",
    )

    allowed_origins: list[str] = field(
        default_factory=lambda: _list_env(
            "ALLOWED_ORIGINS",
            (
                "http://localhost:3000,"
                "http://localhost:5173,"
                "http://localhost:8000,"
                "http://127.0.0.1:3000,"
                "http://127.0.0.1:5173,"
                "http://127.0.0.1:8000"
            ),
        )
    )

    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()