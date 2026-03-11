from pathlib import Path
from typing import ClassVar

from pydantic import AnyUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    url: PostgresDsn | AnyUrl = Field(
        default="postgresql+asyncpg://admin:admin123@postgres:5432/task_service",
        alias="TASK_SERVICE_DATABASE_URL",
    )

    api_gateway_url: str = Field(default="http://api-gateway:8000", alias="API_GATEWAY_URL")

    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
