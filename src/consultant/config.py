from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONSULTANT_",
        env_file=".env",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    service_name: str = "ai-business-consultant"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://consultant:consultant@localhost:5432/consultant"
    embedding_dimensions: int = Field(default=1536, gt=0, le=4096)
    auth_mode: Literal["development", "oidc"] = "development"
    development_auth_secret: str = Field(default="local-development-only", min_length=16)
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
