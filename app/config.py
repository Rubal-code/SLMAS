import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "SLMAS Agent"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/agent.sqlite")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_api_url: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    enable_admin_approval: bool = os.getenv("ENABLE_ADMIN_APPROVAL", "true").lower() == "true"


settings = Settings()
