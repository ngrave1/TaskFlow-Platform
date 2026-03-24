from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    smtp_host: str = Field(alias="SMTP_HOST")
    smtp_port: int = Field(alias="SMTP_PORT")
    smtp_username: str = Field(alias="SMTP_USERNAME")
    smtp_password: str = Field(alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(alias="SMTP_USE_TLS")

    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_password: str = Field(alias="REDIS_PASSWORD")
    redis_db: int = Field(alias="REDIS_DB")

    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
