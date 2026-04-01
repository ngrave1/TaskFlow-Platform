from functools import lru_cache
from typing import Any

from common.config import AppSettings, DatabaseSettings, ServiceUrls
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict
from sqlalchemy.pool import NullPool, QueuePool


class TaskServiceDatabaseSettings(DatabaseSettings):
    @model_validator(mode="after")
    def validate_url(self) -> "TaskServiceDatabaseSettings":
        if not self.task_service_url:
            raise ValueError("TASK_SERVICE_DATABASE_URL must be set")
        return self


class TaskServiceUrls(ServiceUrls):
    pass


class TaskServiceSettings(AppSettings):
    database: TaskServiceDatabaseSettings = Field(default_factory=TaskServiceDatabaseSettings)
    urls: TaskServiceUrls = Field(default_factory=TaskServiceUrls)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return self.database.task_service_url

    @property
    def pool_size(self) -> int:
        return self.database.pool_size

    @property
    def max_overflow(self) -> int:
        return self.database.max_overflow

    @property
    def pool_class(self) -> Any:
        if self.database.pool_class == "NullPool":
            return NullPool

        return QueuePool

    @property
    def echo(self) -> bool:
        return self.database.echo

    @property
    def api_gateway_url(self) -> str:
        return self.urls.api_gateway

    @property
    def user_service_url(self) -> str:
        return self.urls.user_service

    @property
    def notification_service_url(self) -> str:
        return self.urls.notification_service


@lru_cache()
def get_settings() -> TaskServiceSettings:
    return TaskServiceSettings()
