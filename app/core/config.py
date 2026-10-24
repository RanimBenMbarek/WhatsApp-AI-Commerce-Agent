
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    app_name: str = "WhatsApp AI Commerce Agent"
    app_version: str = "0.1.0"
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"
    
    supabase_url: str
    supabase_service_role_key: str
    database_url: str
    openai_api_key: str
    
    seller_name: str | None = None
    seller_address: str | None = None
    seller_contact: str | None = None
    currency: str = "EUR"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()
