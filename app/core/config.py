from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str
    database_url: str

    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    admin_api_key: str

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.72
    

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
