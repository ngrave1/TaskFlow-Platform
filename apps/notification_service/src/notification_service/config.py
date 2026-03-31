from functools import lru_cache

from common.config import AppSettings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SMTPSettings(BaseSettings):
    host: str = Field(alias="SMTP_HOST")
    port: int = Field(alias="SMTP_PORT")
    username: str = Field(alias="SMTP_USERNAME")
    password: str = Field(alias="SMTP_PASSWORD")
    from_email: str = Field(alias="SMTP_FROM_EMAIL")
    use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    model_config = SettingsConfigDict(extra="ignore")


class RedisSettings(BaseSettings):
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: str = Field(default="", alias="REDIS_PASSWORD")
    db: int = Field(default=0, alias="REDIS_DB")

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    model_config = SettingsConfigDict(extra="ignore")


class NotificationServiceSettings(AppSettings):
    smtp: SMTPSettings = Field(default_factory=SMTPSettings)

    redis: RedisSettings = Field(default_factory=RedisSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def redis_url(self) -> str:
        return self.redis.url

    @property
    def api_gateway_url(self) -> str:
        return self.urls.api_gateway


@lru_cache()
def get_settings() -> NotificationServiceSettings:
    return NotificationServiceSettings()
