from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import ClassVar


class DatabaseSettings(BaseSettings):
    USER_URL: str = Field(default="http://user-service:8000", alias="USER_SERVICE_URL")
    TASK_URL: str = Field(default="http://task-service:8000", alias="TASK_SERVICE_URL")
    NOTIFICATION_URL: str = Field(
        default="http://notification-service:8000", alias="NOTIFICATION_SERVICE_URL"
    )
    ANALYTICS_URL: str = Field(
        default="http://analytics-service:8000", alias="ANALYTICS_SERVICE_URL"
    )

    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = DatabaseSettings()
