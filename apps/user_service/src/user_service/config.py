from functools import lru_cache
from pathlib import Path
from typing import Any

from common.config import AppSettings, DatabaseSettings, ServiceUrls
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.pool import NullPool, QueuePool


class UserServiceDatabaseSettings(DatabaseSettings):
    @property
    def url(self) -> str:
        return self.user_service_url


class UserServiceUrls(ServiceUrls):
    pass


class AuthJWT(BaseSettings):
    private_key_path: Path = Field(default=Path(__file__).parent.parent / "certs/jwt-private.pem")
    public_key_path: Path = Field(default=Path(__file__).parent.parent / "certs/jwt-public.pem")
    algorithm: str = "RS256"
    access_token_expire: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE")

    model_config = SettingsConfigDict(extra="ignore")


class UserServiceSettings(AppSettings):
    database: UserServiceDatabaseSettings = Field(default_factory=UserServiceDatabaseSettings)
    urls: UserServiceUrls = Field(default_factory=UserServiceUrls)
    auth_jwt: AuthJWT = Field(default_factory=AuthJWT)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return self.database.user_service_url

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


@lru_cache()
def get_settings() -> UserServiceSettings:
    return UserServiceSettings()
