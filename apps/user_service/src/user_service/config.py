from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    url: str = Field(
        default="postgresql+asyncpg://admin:admin123@postgres:5432/user_service",
        alias="USER_SERVICE_DATABASE_URL",
    )


class AuthJWT(BaseModel):
    private_key_path: Path = Path(__file__).parent.parent / "certs/jwt-private.pem"
    public_key_path: Path = Path(__file__).parent.parent / "certs/jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire: int = Field(default=15)
    refresh_token_expire: int = Field(default=30)


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://admin:admin123@postgres:5432/user_service",
        alias="USER_SERVICE_DATABASE_URL",
    )
    private_key_path: Path = Field(default=Path(__file__).parent.parent / "certs/jwt-private.pem")
    public_key_path: Path = Field(default=Path(__file__).parent.parent / "certs/jwt-public.pem")
    algorithm: str = "RS256"
    env_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=str(env_path / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(url=self.database_url)

    @property
    def auth_jwt(self) -> AuthJWT:
        return AuthJWT(
            private_key_path=self.private_key_path,
            public_key_path=self.public_key_path,
            algorithm=self.algorithm,
        )


settings = Settings()
