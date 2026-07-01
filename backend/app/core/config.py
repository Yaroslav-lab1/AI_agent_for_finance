from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgres_db: str = "finance_agent"
    postgres_user: str = "finance_agent"
    postgres_password: str = "finance_agent_dev_password"
    database_url: str = "postgresql+asyncpg://finance_agent:finance_agent_dev_password@postgres:5432/finance_agent"
    jwt_secret: str = "dev-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    backend_cors_origins: str = "http://localhost:5173"
    llm_provider: str = "mock"
    llm_model: str = "mock-transaction-extractor"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_request_timeout_seconds: int = 60
    ollama_base_url: str = "http://localhost:11434"
    ollama_request_timeout_seconds: int = 120
    ocr_lang: str = "rus+eng"
    max_upload_size_mb: int = 10
    environment: str = Field(default="development")

    @property
    def cors_origins(self) -> list[str | AnyHttpUrl]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
