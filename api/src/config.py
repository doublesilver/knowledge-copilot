import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    embedding_model: str
    chat_model: str
    openai_timeout: int
    cors_origins: list[str]
    db_path: str


def _parse_cors(origins: str) -> list[str]:
    if not origins:
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        openai_timeout=int(os.getenv("OPENAI_REQUEST_TIMEOUT", "30")),
        cors_origins=_parse_cors(os.getenv("CORS_ORIGINS", "*")),
        db_path=os.getenv(
            "KNOWLEDGE_COPILOT_DATABASE_PATH",
            os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_copilot.db"),
        ),
    )
