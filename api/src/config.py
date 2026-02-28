import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    embedding_model: str
    chat_model: str
    api_timeout: int
    cors_origins: list[str]
    db_path: str


def _parse_cors(origins: str) -> list[str]:
    if not origins:
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004"),
        chat_model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
        api_timeout=int(os.getenv("GEMINI_REQUEST_TIMEOUT", "30")),
        cors_origins=_parse_cors(os.getenv("CORS_ORIGINS", "*")),
        db_path=os.getenv(
            "KNOWLEDGE_COPILOT_DATABASE_PATH",
            os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_copilot.db"),
        ),
    )
