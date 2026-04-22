from pathlib import Path
from typing import ClassVar, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    task_service_url: str = Field(alias="TASK_SERVICE_DATABASE_URL")
    user_service_url: str = Field(alias="USER_SERVICE_DATABASE_URL")
    pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    pool_class: Optional[str] = Field(default=None, alias="DATABASE_POOL_CLASS")
    max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    echo: bool = Field(default=False, alias="DATABASE_ECHO")

    model_config = SettingsConfigDict(extra="ignore")


class ServiceUrls(BaseSettings):
    api_gateway: str = Field(default="http://api-gateway:8000", alias="API_GATEWAY_URL")
    user_service: str = Field(default="http://user-service:8000", alias="USER_URL")
    task_service: str = Field(default="http://task-service:8000", alias="TASK_URL")
    notification_service: str = Field(
        default="http://notification-service:8000", alias="NOTIFICATION_URL"
    )
    analytics_service: str = Field(default="http://analytics-service:8000", alias="ANALYTICS_URL")

    model_config = SettingsConfigDict(extra="ignore")


class LoggingSettings(BaseSettings):
    environment: str = Field(alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = SettingsConfigDict(extra="ignore")


class AppSettings(BaseSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    urls: ServiceUrls = Field(default_factory=ServiceUrls)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    environment: str = Field(alias="ENVIRONMENT")
    debug: bool = Field(alias="DEBUG")

    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


_common_settings: Optional[AppSettings] = None


def get_common_settings() -> Optional[AppSettings]:
    global _common_settings
    if _common_settings is None:
        _common_settings = AppSettings()
    return _common_settings


class _LazySettings:
    def __getattr__(self, name):
        settings = get_common_settings()
        if settings is None:
            raise RuntimeError("Common settings not available in test environment")
        return getattr(settings, name)


common_settings = _LazySettings()
