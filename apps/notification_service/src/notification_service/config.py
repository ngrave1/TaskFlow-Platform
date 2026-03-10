from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn
from pathlib import Path
from typing import ClassVar


class Settings(BaseSettings):
    url: PostgresDsn = Field(
        default="postgresql+asyncpg://admin:admin123@postgres:5432/notification_service",
        alias="NOTIFICATION_SERVICE_DATABASE_URL",
    )

    api_gateway_url: str = Field(
        default="http://api-gateway:8000", alias="API_GATEWAY_URL"
    )

    stmp_host: str = Field(default="smtp.mail.ru", alias="SMTP_HOST")

    port: int = Field(
        default=587,
        alias="port",
    )

    username: str = Field(
        default="ngrave79@mail.ru",
        alias="username",
    )

    password: str = Field(
        alias="SMTP_PASSWORD",
    )

    from_email: str = Field(default="ngrave79@mail.ru", alias="from_email")

    env_path: ClassVar[Path] = (
        Path(__file__).parent.parent.parent.parent.parent / ".env"
    )
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
