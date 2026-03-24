from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USER_URL: str = Field(alias="USER_URL")
    TASK_URL: str = Field(alias="TASK_URL")
    NOTIFICATION_URL: str = Field(alias="NOTIFICATION_URL")
    ANALYTICS_URL: str = Field(alias="ANALYTICS_URL")

    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
