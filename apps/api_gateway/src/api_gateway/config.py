from functools import lru_cache

from common.config import AppSettings
from pydantic_settings import SettingsConfigDict


class ApiGatewaySettings(AppSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def user_url(self) -> str:
        return self.urls.user_service

    @property
    def task_url(self) -> str:
        return self.urls.task_service

    @property
    def notification_url(self) -> str:
        return self.urls.notification_service

    @property
    def analytics_url(self) -> str:
        return self.urls.analytics_service

    @property
    def api_gateway_url(self) -> str:
        return self.urls.api_gateway


@lru_cache()
def get_settings() -> ApiGatewaySettings:
    return ApiGatewaySettings()
