import os
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthJWT(BaseModel):
    private_key_path: Path = Path(__file__).parent.parent / "certs/jwt-private.pem"
    public_key_path: Path = Path(__file__).parent.parent / "certs/jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire: int = Field(default=15)
    refresh_token_expire: int = Field(default=30)


class Settings(BaseSettings):
    @property
    def url(self) -> str:
        if os.getenv("TESTING") == "true":
            return os.getenv(
                "USER_SERVICE_DATABASE_URL", "sqlite+aiosqlite:///file::memory:?cache=shared"
            )

        from common.config import get_common_settings

        common = get_common_settings()
        base = common.database.url.rstrip("/")
        if base.endswith("/user_service"):
            return base
        if not base.endswith("/"):
            base = base + "/"
        return f"{base}user_service"

    @property
    def pool_size(self) -> int:
        if os.getenv("TESTING") == "true":
            return 5
        from common.config import get_common_settings

        common = get_common_settings()
        return common.database.pool_size

    @property
    def echo(self) -> bool:
        if os.getenv("TESTING") == "true":
            return False
        from common.config import get_common_settings

        common = get_common_settings()
        return common.database.echo

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
    def auth_jwt(self) -> AuthJWT:
        return AuthJWT(
            private_key_path=self.private_key_path,
            public_key_path=self.public_key_path,
            algorithm=self.algorithm,
        )


settings = Settings()
